import fs from 'node:fs/promises';
import path from 'node:path';
import crypto from 'node:crypto';
import { assertNoCpfPattern } from './log-sanitizer.js';

const ALLOWED_EVENT_KEYS = new Set([
  'audit_id',
  'transaction_id',
  'audit_token_hash',
  'status',
  'issuer',
  'verification',
  'created_at',
  'schema_version',
  'event_hash'
]);

function assertAllowedKeys(event) {
  for (const key of Object.keys(event)) {
    if (!ALLOWED_EVENT_KEYS.has(key)) {
      throw new Error(`AUDIT_EVENT_KEY_BLOCKED:${key}`);
    }
  }
}

export class AuditStore {
  constructor({ ledgerPath = './audit/events.jsonl' } = {}) {
    this.ledgerPath = ledgerPath;
  }

  hashEvent(event) {
    return crypto.createHash('sha256').update(JSON.stringify(event), 'utf8').digest('hex');
  }

  async append(eventInput) {
    const event = {
      ...eventInput,
      schema_version: 'audit-event.v1',
      created_at: new Date().toISOString()
    };

    assertAllowedKeys(event);
    assertNoCpfPattern(event);

    const eventHash = this.hashEvent(event);
    const record = { ...event, event_hash: eventHash };

    assertAllowedKeys(record);
    assertNoCpfPattern(record);

    await fs.mkdir(path.dirname(this.ledgerPath), { recursive: true });
    await fs.appendFile(this.ledgerPath, `${JSON.stringify(record)}\n`, { encoding: 'utf8', mode: 0o600 });

    return { recorded: true, event_hash: eventHash };
  }
}
