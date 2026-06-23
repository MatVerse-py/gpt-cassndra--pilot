import crypto from 'node:crypto';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import express from 'express';
import helmet from 'helmet';
import pino from 'pino';
import Ajv from 'ajv';
import dotenv from 'dotenv';
import { SessionManager, SessionStoreUnavailableError } from './lib/session-manager.js';
import { TrustEngine } from './lib/trust-engine.js';
import { AuditStore } from './lib/audit-store.js';
import { createSafeLogger } from './lib/log-sanitizer.js';

dotenv.config();

const moduleDirectory = path.dirname(fileURLToPath(import.meta.url));
const frontendDirectory = path.resolve(moduleDirectory, '../frontend');

function loadConfig() {
  const configPath = process.env.CIN_ROUTER_CONFIG || './config.example.json';
  if (fs.existsSync(configPath)) {
    return JSON.parse(fs.readFileSync(configPath, 'utf8'));
  }
  return {};
}

function parseIssuerStates(value, fallback) {
  if (!value) return fallback;
  return value.split(',').map((item) => item.trim().toUpperCase()).filter(Boolean);
}

function httpStatusForGate(gate) {
  if (gate === 'PASS') return 200;
  if (gate === 'HOLD') return 202;
  if (gate === 'ESCALATE') return 409;
  return 400;
}

function isAuditFailure(error) {
  return /^AUDIT_|^SENSITIVE_/.test(error?.message || '');
}

const config = loadConfig();
const port = Number(process.env.PORT || config.port || 3001);
const mode = process.env.TRUST_ROUTER_MODE || config.trust_router_mode || 'sandbox';
const redisUrl = process.env.REDIS_URL || config.redis_url || '';
const auditLedgerPath = process.env.AUDIT_LEDGER_PATH || config.audit_ledger_path || './audit/events.jsonl';
const trustedIssuerStates = parseIssuerStates(process.env.TRUSTED_ISSUER_STATES, config.trusted_issuer_states);

const logger = createSafeLogger(pino({ level: process.env.LOG_LEVEL || 'info' }));
const sessionManager = new SessionManager({ redisUrl });
const trustEngine = new TrustEngine({ mode, trustedIssuerStates });
const auditStore = new AuditStore({ ledgerPath: auditLedgerPath });
const ajv = new Ajv({ allErrors: true });

const validateRequest = ajv.compile({
  type: 'object',
  additionalProperties: false,
  required: ['sessionId', 'cpf', 'issuerState'],
  properties: {
    sessionId: {
      type: 'string',
      pattern: '^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[1-5][0-9a-fA-F]{3}-[89abAB][0-9a-fA-F]{3}-[0-9a-fA-F]{12}$'
    },
    cpf: { type: 'string', minLength: 11, maxLength: 14 },
    issuerState: { type: 'string', pattern: '^[A-Za-z]{2}$' }
  }
});

const app = express();
app.disable('x-powered-by');
app.use(helmet());
app.use(express.json({ limit: '16kb', strict: true }));
app.get('/', (_req, res) => res.redirect(302, '/demo/'));
app.use('/demo', express.static(frontendDirectory, { index: 'wallet-demo.html', maxAge: '1h' }));

app.get('/health', (_req, res) => {
  res.json({ ok: true, service: 'cin-digital-trust-router', mode });
});

app.post('/api/session/start', async (_req, res) => {
  try {
    const session = await sessionManager.createSession();
    return res.status(201).json({ sessionId: session.sessionId, ttlSeconds: session.ttlSeconds });
  } catch (error) {
    logger.error('session creation held', error);
    return res.status(503).json({
      status: 'UNVERIFIED',
      gate: 'HOLD',
      reason: 'SESSION_STORE_UNAVAILABLE'
    });
  }
});

app.post('/api/cin/validate', async (req, res) => {
  const body = req.body ?? {};

  if (!validateRequest(body)) {
    logger.warn('validation request schema rejected', { errors: validateRequest.errors });
    return res.status(400).json({ status: 'INVALID', gate: 'BLOCK', reason: 'INVALID_REQUEST_SCHEMA' });
  }

  const transactionId = crypto.randomUUID();
  const auditId = crypto.randomUUID();
  const issuerState = body.issuerState.toUpperCase();

  try {
    const sessionSalt = await sessionManager.consumeSalt(body.sessionId);
    if (!sessionSalt) {
      return res.status(401).json({ status: 'UNVERIFIED', gate: 'BLOCK', reason: 'SESSION_EXPIRED_OR_REUSED' });
    }

    const auditToken = trustEngine.generateAuditToken({
      cpfInput: body.cpf,
      sessionSalt,
      transactionId
    });

    const auditTokenHash = trustEngine.createStorageFingerprint(auditToken);
    const federated = await trustEngine.verifyFederatedStatus({ auditToken, issuerState });
    const event = {
      audit_id: auditId,
      transaction_id: transactionId,
      audit_token_hash: auditTokenHash,
      status: federated.status,
      gate: federated.gate,
      reason: federated.reason,
      issuer: {
        country: 'BR',
        state_code: issuerState,
        agency_id: mode === 'sandbox' ? `SANDBOX-${issuerState}-001` : `OFFICIAL-${issuerState}`
      },
      verification: {
        cpf_format_valid: true,
        issuer_trusted: federated.issuerTrusted,
        signature_valid: federated.signatureValid,
        source: federated.source
      }
    };

    const auditResult = await auditStore.append(event);

    return res.status(httpStatusForGate(federated.gate)).json({
      status: federated.status,
      gate: federated.gate,
      reason: federated.reason,
      issuer: event.issuer,
      verification: event.verification,
      audit: {
        audit_id: auditId,
        transaction_id: transactionId,
        audit_token_hash: auditTokenHash,
        previous_event_hash: auditResult.previous_event_hash,
        recorded: auditResult.recorded,
        event_hash: auditResult.event_hash
      }
    });
  } catch (error) {
    if (error instanceof SessionStoreUnavailableError) {
      logger.error('validation held because session store is unavailable', error, { transactionId, auditId });
      return res.status(503).json({
        status: 'UNVERIFIED',
        gate: 'HOLD',
        reason: 'SESSION_STORE_UNAVAILABLE'
      });
    }

    if (isAuditFailure(error)) {
      logger.error('validation escalated because audit evidence failed', error, { transactionId, auditId });
      return res.status(409).json({
        status: 'UNVERIFIED',
        gate: 'ESCALATE',
        reason: 'AUDIT_EVIDENCE_UNAVAILABLE'
      });
    }

    logger.error('cin validation blocked', error, { transactionId, auditId });
    return res.status(400).json({ status: 'INVALID', gate: 'BLOCK', reason: error.message });
  } finally {
    if (typeof body.cpf === 'string') {
      body.cpf = '';
    }
  }
});

app.listen(port, () => {
  logger.info('cin digital trust router started', { port, mode, demo: '/demo/' });
});
