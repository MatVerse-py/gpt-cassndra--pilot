import fs from 'node:fs/promises';
import path from 'node:path';
import crypto from 'node:crypto';
import { assertSafeAuditPayload } from './log-sanitizer.js';

const GENESIS_HASH = '0'.repeat(64);
const ALLOWED_EVENT_KEYS = new Set([
  'audit_id',
  'transaction_id',
  'audit_token_hash',
  'status',
  'gate',
  'reason',
  'issuer',
  'verification',
  'created_at',
  'schema_version',
  'previous_event_hash',
  'event_hash'
]);

function assertAllowedKeys(event) {
  for (const key of Object.keys(event)) {
    if (!ALLOWED_EVENT_KEYS.has(key)) {
      throw new Error(`AUDIT_EVENT_KEY_BLOCKED:${key}`);
    }
  }
}

function canonicalize(value) {
  if (Array.isArray(value)) {
    return `[${value.map((item) => canonicalize(item)).join(',')}]`;
  }

  if (value && typeof value === 'object') {
    return `{${Object.keys(value)
      .sort()
      .map((key) => `${JSON.stringify(key)}:${canonicalize(value[key])}`)
      .join(',')}}`;
  }

  return JSON.stringify(value);
}

function lastNonEmptyLine(content) {
  return content.split('\n').map((line) => line.trim()).filter(Boolean).at(-1) || '';
}

export class AuditStore {
  constructor({ ledgerPath = './audit/events.jsonl' } = {}) {
    this.ledgerPath = ledgerPath;
    this.writeQueue = Promise.resolve();
  }

  hashEvent(event) {
    return crypto.createHash('sha256').update(canonicalize(event), 'utf8').digest('hex');
  }

  async append(eventInput) {
    const operation = this.writeQueue.then(() => this.#appendSerialized(eventInput));
    this.writeQueue = operation.catch(() => undefined);
    return operation;
  }

  async #appendSerialized(eventInput) {
    if ('event_hash' in eventInput || 'previous_event_hash' in eventInput) {
      throw new Error('AUDIT_HASH_FIELDS_ARE_SYSTEM_MANAGED');
    }

    assertAllowedKeys(eventInput);
    assertSafeAuditPayload(eventInput);

    await fs.mkdir(path.dirname(this.ledgerPath), { recursive: true, mode: 0o700 });
    const previousEventHash = await this.#readHead();
    const event = {
      ...eventInput,
      schema_version: 'audit-event.v1',
      created_at: new Date().toISOString(),
      previous_event_hash: previousEventHash
    };

    assertAllowedKeys(event);
    assertSafeAuditPayload(event);

    const eventHash = this.hashEvent(event);
    const record = { ...event, event_hash: eventHash };

    assertAllowedKeys(record);
    assertSafeAuditPayload(record);

    const file = await fs.open(this.ledgerPath, 'a', 0o600);
    try {
      await file.writeFile(`${JSON.stringify(record)}\n`, 'utf8');
      await file.sync();
    } finally {
      await file.close();
    }

    return {
      recorded: true,
      event_hash: eventHash,
      previous_event_hash: previousEventHash
    };
  }

  async #readHead() {
    try {
      const content = await fs.readFile(this.ledgerPath, 'utf8');
      const line = lastNonEmptyLine(content);
      if (!line) return GENESIS_HASH;

      const record = JSON.parse(line);
      if (!/^[a-f0-9]{64}$/.test(record.event_hash || '')) {
        throw new Error('AUDIT_LEDGER_HEAD_INVALID');
      }
      return record.event_hash;
    } catch (error) {
      if (error?.code === 'ENOENT') return GENESIS_HASH;
      throw error;
    }
  }

  async verify() {
    let content = '';
    try {
      content = await fs.readFile(this.ledgerPath, 'utf8');
    } catch (error) {
      if (error?.code === 'ENOENT') {
        return { valid: true, records: 0, head: GENESIS_HASH };
      }
      throw error;
    }

    let previousEventHash = GENESIS_HASH;
    let records = 0;

    for (const line of content.split('\n').map((item) => item.trim()).filter(Boolean)) {
      const record = JSON.parse(line);
      assertAllowedKeys(record);
      assertSafeAuditPayload(record);

      const { event_hash: eventHash, ...event } = record;
      if (event.previous_event_hash !== previousEventHash) {
        return { valid: false, records, head: previousEventHash, reason: 'CHAIN_LINK_MISMATCH' };
      }
      if (this.hashEvent(event) !== eventHash) {
        return { valid: false, records, head: previousEventHash, reason: 'EVENT_HASH_MISMATCH' };
      }

      previousEventHash = eventHash;
      records += 1;
    }

    return { valid: true, records, head: previousEventHash };
  }
}
