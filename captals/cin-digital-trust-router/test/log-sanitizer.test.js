import test from 'node:test';
import assert from 'node:assert/strict';
import { assertNoCpfPattern, sanitizeValue } from '../src/lib/log-sanitizer.js';

function maskedIdentifierFixture() {
  return ['111', '444', '777', '35'].join('.').replace(/\.(\d{2})$/, '-$1');
}

test('sanitizes masked and raw identifier patterns', () => {
  const raw = maskedIdentifierFixture().replace(/\D/g, '');
  const output = sanitizeValue({ masked: maskedIdentifierFixture(), raw });
  assert.equal(output.masked, '***.***.***-**');
  assert.equal(output.raw, '***********');
});

test('blocks sensitive identifier patterns in audit payloads', () => {
  assert.throws(() => assertNoCpfPattern({ value: maskedIdentifierFixture() }), /SENSITIVE_IDENTIFIER_PATTERN_BLOCKED/);
  assert.throws(() => assertNoCpfPattern({ value: maskedIdentifierFixture().replace(/\D/g, '') }), /SENSITIVE_IDENTIFIER_PATTERN_BLOCKED/);
});

test('allows storage-safe audit payload', () => {
  assert.doesNotThrow(() => assertNoCpfPattern({ audit_token_hash: 'a'.repeat(64), status: 'VALID' }));
});
