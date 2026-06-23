import crypto from 'node:crypto';
import fs from 'node:fs';
import express from 'express';
import cors from 'cors';
import helmet from 'helmet';
import pino from 'pino';
import Ajv from 'ajv';
import dotenv from 'dotenv';
import { SessionManager } from './lib/session-manager.js';
import { TrustEngine } from './lib/trust-engine.js';
import { AuditStore } from './lib/audit-store.js';
import { createSafeLogger } from './lib/log-sanitizer.js';

dotenv.config();

function loadConfig() {
  const configPath = process.env.CIN_ROUTER_CONFIG || './config.example.json';
  if (fs.existsSync(configPath)) {
    return JSON.parse(fs.readFileSync(configPath, 'utf8'));
  }
  return {};
}

const config = loadConfig();
const port = Number(process.env.PORT || config.port || 3001);
const mode = process.env.TRUST_ROUTER_MODE || config.trust_router_mode || 'sandbox';
const redisUrl = process.env.REDIS_URL || config.redis_url || '';
const auditLedgerPath = process.env.AUDIT_LEDGER_PATH || config.audit_ledger_path || './audit/events.jsonl';

const logger = createSafeLogger(pino({ level: process.env.LOG_LEVEL || 'info' }));
const sessionManager = new SessionManager({ redisUrl });
const trustEngine = new TrustEngine({ mode, trustedIssuerStates: config.trusted_issuer_states });
const auditStore = new AuditStore({ ledgerPath: auditLedgerPath });
const ajv = new Ajv({ allErrors: true });

const validateRequest = ajv.compile({
  type: 'object',
  additionalProperties: false,
  required: ['sessionId', 'cpf', 'issuerState'],
  properties: {
    sessionId: { type: 'string', minLength: 8, maxLength: 128 },
    cpf: { type: 'string', minLength: 11, maxLength: 14 },
    issuerState: { type: 'string', minLength: 2, maxLength: 2 }
  }
});

const app = express();
app.use(helmet());
app.use(cors({ origin: false }));
app.use(express.json({ limit: '16kb' }));

app.get('/health', (_req, res) => {
  res.json({ ok: true, service: 'cin-digital-trust-router', mode });
});

app.post('/api/session/start', async (_req, res) => {
  const session = await sessionManager.createSession();
  res.status(201).json({ sessionId: session.sessionId, ttlSeconds: session.ttlSeconds });
});

app.post('/api/cin/validate', async (req, res) => {
  const body = req.body ?? {};

  if (!validateRequest(body)) {
    logger.warn('validation request schema rejected', { errors: validateRequest.errors });
    return res.status(400).json({ status: 'BLOCK', error: 'INVALID_REQUEST_SCHEMA' });
  }

  const transactionId = crypto.randomUUID();
  const auditId = crypto.randomUUID();
  const issuerState = body.issuerState.toUpperCase();

  try {
    const sessionSalt = await sessionManager.consumeSalt(body.sessionId);
    if (!sessionSalt) {
      return res.status(401).json({ status: 'BLOCK', error: 'SESSION_EXPIRED_OR_REUSED' });
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

    return res.status(federated.status === 'VALID' ? 200 : 202).json({
      status: federated.status,
      issuer: event.issuer,
      verification: event.verification,
      audit: {
        audit_id: auditId,
        transaction_id: transactionId,
        audit_token_hash: auditTokenHash,
        recorded: auditResult.recorded,
        event_hash: auditResult.event_hash
      }
    });
  } catch (error) {
    logger.error('cin validation blocked', error, { transactionId, auditId });
    return res.status(400).json({ status: 'BLOCK', error: error.message });
  }
});

app.listen(port, () => {
  logger.info('cin digital trust router started', { port, mode });
});
