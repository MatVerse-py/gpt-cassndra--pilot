import test from 'node:test';
import assert from 'node:assert/strict';
import { assertNoCpfPattern, assertSafeAuditPayload, sanitizeValue } from '../src/lib/log-sanitizer.js';

function maskedIdentifierFixture() {
  return ['123', '456', '789', '09'].join('.').replace(/\.(\d{2})$/, '-$1');
}

test('sanitizes masked and raw identifier patterns', () => {
  const raw = maskedIdentifierFixture().replace(/\D/g, '');
  const output = sanitizeValue({ masked: maskedIdentifierFixture(), raw });
  assert.equal(output.masked, '***.***.***-**');
  assert.equal(output.raw, '***********');
});

test('redacts sensitive field values even when their content is not a full identifier', () => {
  const output = sanitizeValue({ cpf: 'partial-value', nested: { document_number: 'opaque-value' } });
  assert.equal(output.cpf, '[REDACTED]');
  assert.equal(output.nested.document_number, '[REDACTED]');
});

test('blocks sensitive identifier patterns and fields in audit payloads', () => {
  assert.throws(() => assertNoCpfPattern({ value: maskedIdentifierFixture() }), /SENSITIVE_IDENTIFIER_PATTERN_BLOCKED/);
  assert.throws(() => assertNoCpfPattern({ value: maskedIdentifierFixture().replace(/\D/g, '') }), /SENSITIVE_IDENTIFIER_PATTERN_BLOCKED/);
  assert.throws(() => assertSafeAuditPayload({ cpf: 'opaque-value' }), /SENSITIVE_FIELD_BLOCKED/);
});

test('allows storage-safe audit payload', () => {
  assert.doesNotThrow(() => assertSafeAuditPayload({ audit_token_hash: 'a'.repeat(64), status: 'UNVERIFIED', gate: 'HOLD' }));
});
