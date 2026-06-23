import test from 'node:test';
import assert from 'node:assert/strict';
import crypto from 'node:crypto';
import { TrustEngine } from '../src/lib/trust-engine.js';

function validCpfFixture() {
  return ['111', '444', '777', '35'].join('.').replace(/\.(\d{2})$/, '-$1');
}

test('validates CPF algorithm without persistence', () => {
  const engine = new TrustEngine();
  assert.equal(engine.validateCpfAlgorithm(validCpfFixture()), true);
  assert.equal(engine.validateCpfAlgorithm('1'.repeat(11)), false);
  assert.equal(engine.validateCpfAlgorithm('0'.repeat(11)), false);
});

test('generates deterministic audit token for same transaction and salt', () => {
  const engine = new TrustEngine();
  const sessionSalt = crypto.randomBytes(32).toString('hex');
  const transactionId = crypto.randomUUID();
  const first = engine.generateAuditToken({ cpfInput: validCpfFixture(), sessionSalt, transactionId });
  const second = engine.generateAuditToken({ cpfInput: validCpfFixture().replace(/\D/g, ''), sessionSalt, transactionId });
  assert.equal(first, second);
  assert.match(first, /^[a-f0-9]{64}$/);
});

test('uses transaction id to prevent audit token replay equivalence', () => {
  const engine = new TrustEngine();
  const sessionSalt = crypto.randomBytes(32).toString('hex');
  const first = engine.generateAuditToken({ cpfInput: validCpfFixture(), sessionSalt, transactionId: crypto.randomUUID() });
  const second = engine.generateAuditToken({ cpfInput: validCpfFixture(), sessionSalt, transactionId: crypto.randomUUID() });
  assert.notEqual(first, second);
});

test('holds non-sandbox mode until official connector exists', async () => {
  const engine = new TrustEngine({ mode: 'production', trustedIssuerStates: ['SP'] });
  const result = await engine.verifyFederatedStatus({ auditToken: 'a'.repeat(64), issuerState: 'SP' });
  assert.equal(result.status, 'HOLD');
  assert.equal(result.source, 'official-connector-required');
});
