const CPF_MASKED_PATTERN = /\b\d{3}\.\d{3}\.\d{3}-\d{2}\b/g;
const CPF_RAW_PATTERN = /(?<!\d)\d{11}(?!\d)/g;

export function sanitizeValue(value) {
  if (typeof value === 'string') {
    return value
      .replace(CPF_MASKED_PATTERN, '***.***.***-**')
      .replace(CPF_RAW_PATTERN, '***********');
  }

  if (Array.isArray(value)) {
    return value.map((item) => sanitizeValue(item));
  }

  if (value && typeof value === 'object') {
    return Object.fromEntries(
      Object.entries(value).map(([key, item]) => [key, sanitizeValue(item)])
    );
  }

  return value;
}

export function assertNoCpfPattern(payload) {
  const serialized = JSON.stringify(payload);
  if (CPF_MASKED_PATTERN.test(serialized) || CPF_RAW_PATTERN.test(serialized)) {
    throw new Error('SENSITIVE_IDENTIFIER_PATTERN_BLOCKED');
  }
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
