import test from 'node:test';
import assert from 'node:assert/strict';
import crypto from 'node:crypto';
import { TrustEngine } from '../src/lib/trust-engine.js';

function validIdentifierFixture() {
  return ['123', '456', '789', '09'].join('');
}

test('validates identifier algorithm without persistence', () => {
  const engine = new TrustEngine();
  assert.equal(engine.validateCpfAlgorithm(validIdentifierFixture()), true);
  assert.equal(engine.validateCpfAlgorithm('1'.repeat(11)), false);
  assert.equal(engine.validateCpfAlgorithm('0'.repeat(11)), false);
});

test('generates deterministic audit token for same transaction and salt', () => {
  const engine = new TrustEngine();
  const sessionSalt = crypto.randomBytes(32).toString('hex');
  const transactionId = crypto.randomUUID();
  const first = engine.generateAuditToken({ cpfInput: validIdentifierFixture(), sessionSalt, transactionId });
  const second = engine.generateAuditToken({ cpfInput: validIdentifierFixture(), sessionSalt, transactionId });
  assert.equal(first, second);
  assert.match(first, /^[a-f0-9]{64}$/);
});

test('uses transaction id to prevent audit token replay equivalence', () => {
  const engine = new TrustEngine();
  const sessionSalt = crypto.randomBytes(32).toString('hex');
  const first = engine.generateAuditToken({ cpfInput: validIdentifierFixture(), sessionSalt, transactionId: crypto.randomUUID() });
  const second = engine.generateAuditToken({ cpfInput: validIdentifierFixture(), sessionSalt, transactionId: crypto.randomUUID() });
  assert.notEqual(first, second);
});

test('sandbox preserves hold until official assurance exists', async () => {
  const engine = new TrustEngine({ mode: 'sandbox', trustedIssuerStates: ['SP'] });
  const result = await engine.verifyFederatedStatus({ auditToken: 'a'.repeat(64), issuerState: 'SP' });
  assert.equal(result.status, 'UNVERIFIED');
  assert.equal(result.gate, 'HOLD');
  assert.equal(result.reason, 'SANDBOX_NO_OFFICIAL_ASSURANCE');
  assert.equal(result.signatureValid, false);
});

test('non-sandbox preserves hold until official connector exists', async () => {
  const engine = new TrustEngine({ mode: 'production', trustedIssuerStates: ['SP'] });
  const result = await engine.verifyFederatedStatus({ auditToken: 'a'.repeat(64), issuerState: 'SP' });
  assert.equal(result.status, 'UNVERIFIED');
  assert.equal(result.gate, 'HOLD');
  assert.equal(result.reason, 'OFFICIAL_CONNECTOR_REQUIRED');
});

test('unknown issuer is blocked before assurance is claimed', async () => {
  const engine = new TrustEngine({ mode: 'sandbox', trustedIssuerStates: ['SP'] });
  const result = await engine.verifyFederatedStatus({ auditToken: 'a'.repeat(64), issuerState: 'ZZ' });
  assert.equal(result.status, 'INVALID');
  assert.equal(result.gate, 'BLOCK');
  assert.equal(result.reason, 'UNTRUSTED_ISSUER');
});
