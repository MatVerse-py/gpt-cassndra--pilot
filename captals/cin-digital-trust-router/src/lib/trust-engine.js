import crypto from 'node:crypto';

const CPF_ALLOWED_CHARS = /[^\d]+/g;
const VALID_STATES = new Set([
  'AC', 'AL', 'AP', 'AM', 'BA', 'CE', 'DF', 'ES', 'GO', 'MA', 'MT', 'MS',
  'MG', 'PA', 'PB', 'PR', 'PE', 'PI', 'RJ', 'RN', 'RS', 'RO', 'RR', 'SC',
  'SP', 'SE', 'TO'
]);

export class TrustEngine {
  constructor({ mode = 'sandbox', trustedIssuerStates = [...VALID_STATES] } = {}) {
    this.mode = mode;
    this.trustedIssuerStates = new Set(trustedIssuerStates);
  }

  normalizeCpf(cpfInput) {
    if (typeof cpfInput !== 'string') {
      throw new Error('CPF_MUST_BE_STRING');
    }
    return cpfInput.replace(CPF_ALLOWED_CHARS, '');
  }

  validateCpfAlgorithm(cpfInput) {
    const cpf = this.normalizeCpf(cpfInput);

    if (cpf.length !== 11 || /^(\d)\1{10}$/.test(cpf)) {
      return false;
    }

    let sum = 0;
    for (let i = 0; i < 9; i += 1) {
      sum += Number.parseInt(cpf[i], 10) * (10 - i);
    }
    let firstDigit = 11 - (sum % 11);
    if (firstDigit >= 10) firstDigit = 0;
    if (firstDigit !== Number.parseInt(cpf[9], 10)) return false;

    sum = 0;
    for (let i = 0; i < 10; i += 1) {
      sum += Number.parseInt(cpf[i], 10) * (11 - i);
    }
    let secondDigit = 11 - (sum % 11);
    if (secondDigit >= 10) secondDigit = 0;

    return secondDigit === Number.parseInt(cpf[10], 10);
  }

  generateAuditToken({ cpfInput, sessionSalt, transactionId }) {
    const cpf = this.normalizeCpf(cpfInput);

    if (!this.validateCpfAlgorithm(cpf)) {
      throw new Error('INVALID_CPF_FORMAT');
    }

    if (!/^[a-f0-9]{64}$/i.test(sessionSalt)) {
      throw new Error('INVALID_SESSION_SALT');
    }

    const hmac = crypto.createHmac('sha256', Buffer.from(sessionSalt, 'hex'));
    hmac.update(`${cpf}:${transactionId}`, 'utf8');
    return hmac.digest('hex');
  }

  createStorageFingerprint(auditToken) {
    return crypto.createHash('sha256').update(auditToken, 'utf8').digest('hex');
  }

  verifyIssuer(issuerState) {
    const state = String(issuerState || '').toUpperCase();
    return VALID_STATES.has(state) && this.trustedIssuerStates.has(state);
  }

  async verifyFederatedStatus({ auditToken, issuerState }) {
    const issuerTrusted = this.verifyIssuer(issuerState);
    const tokenWellFormed = /^[a-f0-9]{64}$/i.test(auditToken);

    if (!issuerTrusted || !tokenWellFormed) {
      return {
        status: 'INVALID',
        gate: 'BLOCK',
        reason: !issuerTrusted ? 'UNTRUSTED_ISSUER' : 'INVALID_AUDIT_TOKEN',
        source: this.mode,
        issuerTrusted,
        signatureValid: false
      };
    }

    if (this.mode === 'sandbox') {
      return {
        status: 'UNVERIFIED',
        gate: 'HOLD',
        reason: 'SANDBOX_NO_OFFICIAL_ASSURANCE',
        source: 'sandbox',
        issuerTrusted,
        signatureValid: false
      };
    }

    return {
      status: 'UNVERIFIED',
      gate: 'HOLD',
      reason: 'OFFICIAL_CONNECTOR_REQUIRED',
      source: 'official-connector-required',
      issuerTrusted,
      signatureValid: false
    };
  }
}
