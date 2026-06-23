import test from 'node:test';
import assert from 'node:assert/strict';
import crypto from 'node:crypto';
import fs from 'node:fs/promises';
import os from 'node:os';
import path from 'node:path';
import { AuditStore } from '../src/lib/audit-store.js';

function auditEvent(overrides = {}) {
  return {
    audit_id: crypto.randomUUID(),
    transaction_id: crypto.randomUUID(),
    audit_token_hash: crypto.createHash('sha256').update(crypto.randomUUID()).digest('hex'),
    status: 'UNVERIFIED',
    gate: 'HOLD',
    reason: 'SANDBOX_NO_OFFICIAL_ASSURANCE',
    issuer: { country: 'BR', state_code: 'SP', agency_id: 'SANDBOX-SP-001' },
    verification: {
      cpf_format_valid: true,
      issuer_trusted: true,
      signature_valid: false,
      source: 'sandbox'
    },
    ...overrides
  };
}

test('chains audit records and verifies a clean ledger', async () => {
  const directory = await fs.mkdtemp(path.join(os.tmpdir(), 'cin-audit-'));
  const ledgerPath = path.join(directory, 'events.jsonl');
  const store = new AuditStore({ ledgerPath });

  try {
    const first = await store.append(auditEvent());
    const second = await store.append(auditEvent());

    assert.equal(first.previous_event_hash, '0'.repeat(64));
    assert.equal(second.previous_event_hash, first.event_hash);
    assert.deepEqual(await store.verify(), { valid: true, records: 2, head: second.event_hash });
  } finally {
    await fs.rm(directory, { recursive: true, force: true });
  }
});

test('detects tampering in a persisted ledger record', async () => {
  const directory = await fs.mkdtemp(path.join(os.tmpdir(), 'cin-audit-'));
  const ledgerPath = path.join(directory, 'events.jsonl');
  const store = new AuditStore({ ledgerPath });

  try {
    await store.append(auditEvent());
    const original = await fs.readFile(ledgerPath, 'utf8');
    await fs.writeFile(ledgerPath, original.replace('SANDBOX_NO_OFFICIAL_ASSURANCE', 'TAMPERED_REASON'), 'utf8');

    const result = await store.verify();
    assert.equal(result.valid, false);
    assert.equal(result.reason, 'EVENT_HASH_MISMATCH');
  } finally {
    await fs.rm(directory, { recursive: true, force: true });
  }
});
