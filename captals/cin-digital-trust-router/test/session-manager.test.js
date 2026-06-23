import test from 'node:test';
import assert from 'node:assert/strict';
import { SessionManager } from '../src/lib/session-manager.js';

test('consumes an in-memory session salt only once', async () => {
  const manager = new SessionManager({ redisUrl: '', allowMemoryFallback: true, ttlSeconds: 60 });
  const session = await manager.createSession();
  const first = await manager.consumeSalt(session.sessionId);
  const second = await manager.consumeSalt(session.sessionId);

  assert.match(first, /^[a-f0-9]{64}$/);
  assert.equal(second, null);
});
