import crypto from 'node:crypto';
import Redis from 'ioredis';

const DEFAULT_TTL_SECONDS = 900;

class MemorySaltStore {
  constructor() {
    this.records = new Map();
  }

  async set(sessionId, salt, ttlSeconds) {
    const expiresAt = Date.now() + ttlSeconds * 1000;
    this.records.set(sessionId, { salt, expiresAt });
  }

  async consume(sessionId) {
    const record = this.records.get(sessionId);
    this.records.delete(sessionId);

    if (!record || record.expiresAt < Date.now()) {
      return null;
    }

    return record.salt;
  }
}

export class SessionManager {
  constructor({ redisUrl, ttlSeconds = DEFAULT_TTL_SECONDS } = {}) {
    this.ttlSeconds = ttlSeconds;
    this.memoryStore = new MemorySaltStore();
    this.redis = null;

    if (redisUrl) {
      this.redis = new Redis(redisUrl, {
        lazyConnect: true,
        maxRetriesPerRequest: 1,
        enableOfflineQueue: false
      });
    }
  }

  async createSession() {
    const sessionId = crypto.randomUUID();
    const salt = crypto.randomBytes(32).toString('hex');

    if (this.redis) {
      try {
        if (this.redis.status === 'wait') {
          await this.redis.connect();
        }
        await this.redis.set(`cin:salt:${sessionId}`, salt, 'EX', this.ttlSeconds);
        return { sessionId, ttlSeconds: this.ttlSeconds, storage: 'redis' };
      } catch {
        await this.memoryStore.set(sessionId, salt, this.ttlSeconds);
        return { sessionId, ttlSeconds: this.ttlSeconds, storage: 'memory-fallback' };
      }
    }

    await this.memoryStore.set(sessionId, salt, this.ttlSeconds);
    return { sessionId, ttlSeconds: this.ttlSeconds, storage: 'memory' };
  }

  async consumeSalt(sessionId) {
    if (!sessionId || typeof sessionId !== 'string') {
      return null;
    }

    if (this.redis) {
      try {
        if (this.redis.status === 'wait') {
          await this.redis.connect();
        }
        const key = `cin:salt:${sessionId}`;
        const salt = await this.redis.get(key);
        if (salt) {
          await this.redis.del(key);
          return salt;
        }
      } catch {
        return this.memoryStore.consume(sessionId);
      }
    }

    return this.memoryStore.consume(sessionId);
  }
}
