import process from 'node:process';
import { AuditStore } from '../src/lib/audit-store.js';

const ledgerPath = process.env.AUDIT_LEDGER_PATH || './audit/events.jsonl';
const auditStore = new AuditStore({ ledgerPath });

try {
  const result = await auditStore.verify();
  process.stdout.write(`${JSON.stringify(result)}\n`);
  process.exitCode = result.valid ? 0 : 1;
} catch (error) {
  process.stderr.write(`${JSON.stringify({ valid: false, reason: error.message })}\n`);
  process.exitCode = 1;
}
