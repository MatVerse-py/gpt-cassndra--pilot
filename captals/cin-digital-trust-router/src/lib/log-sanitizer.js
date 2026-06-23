const CPF_MASKED_REPLACE = /\b\d{3}\.\d{3}\.\d{3}-\d{2}\b/g;
const CPF_RAW_REPLACE = /(?<!\d)\d{11}(?!\d)/g;
const CPF_MASKED_DETECT = /\b\d{3}\.\d{3}\.\d{3}-\d{2}\b/;
const CPF_RAW_DETECT = /(?<!\d)\d{11}(?!\d)/;
const FORBIDDEN_FIELD_NAMES = new Set([
  'cpf',
  'cpf_raw',
  'document_number',
  'national_id',
  'personal_identifier'
]);

function normalizedKey(key) {
  return String(key).trim().toLowerCase();
}

function isForbiddenFieldName(key) {
  return FORBIDDEN_FIELD_NAMES.has(normalizedKey(key));
}

export function sanitizeValue(value, key = '') {
  if (isForbiddenFieldName(key)) {
    return '[REDACTED]';
  }

  if (typeof value === 'string') {
    return value
      .replace(CPF_MASKED_REPLACE, '***.***.***-**')
      .replace(CPF_RAW_REPLACE, '***********');
  }

  if (Array.isArray(value)) {
    return value.map((item) => sanitizeValue(item));
  }

  if (value && typeof value === 'object') {
    return Object.fromEntries(
      Object.entries(value).map(([entryKey, item]) => [entryKey, sanitizeValue(item, entryKey)])
    );
  }

  return value;
}

export function assertNoSensitiveFields(value) {
  if (Array.isArray(value)) {
    value.forEach((item) => assertNoSensitiveFields(item));
    return;
  }

  if (!value || typeof value !== 'object') {
    return;
  }

  for (const [key, item] of Object.entries(value)) {
    if (isForbiddenFieldName(key)) {
      throw new Error(`SENSITIVE_FIELD_BLOCKED:${key}`);
    }
    assertNoSensitiveFields(item);
  }
}

export function assertNoCpfPattern(payload) {
  const serialized = JSON.stringify(payload);
  if (CPF_MASKED_DETECT.test(serialized) || CPF_RAW_DETECT.test(serialized)) {
    throw new Error('SENSITIVE_IDENTIFIER_PATTERN_BLOCKED');
  }
}

export function assertSafeAuditPayload(payload) {
  assertNoSensitiveFields(payload);
  assertNoCpfPattern(payload);
}

export function createSafeLogger(baseLogger) {
  return {
    info(message, data = {}) {
      baseLogger.info(sanitizeValue(data), message);
    },
    warn(message, data = {}) {
      baseLogger.warn(sanitizeValue(data), message);
    },
    error(message, error, data = {}) {
      baseLogger.error(sanitizeValue({ ...data, error: error?.message ?? String(error) }), message);
    }
  };
}
