import crypto from 'node:crypto';
import Redis from 'ioredis';

const DEFAULT_TTL_SECONDS = 900;

export class SessionStoreUnavailableError extends Error {
  constructor() {
    super('SESSION_STORE_UNAVAILABLE');
    this.name = 'SessionStoreUnavailableError';
  }
}

class MemorySaltStore {
  constructor() {
    this.records = new Map();
  }

  pruneExpired(now = Date.now()) {
    for (const [sessionId, record] of this.records.entries()) {
      if (record.expiresAt <= now) {
        this.records.delete(sessionId);
      }
    }
  }

  async set(sessionId, salt, ttlSeconds) {
    this.pruneExpired();
    this.records.set(sessionId, { salt, expiresAt: Date.now() + ttlSeconds * 1000 });
  }

  async consume(sessionId) {
    this.pruneExpired();
    const record = this.records.get(sessionId);
    this.records.delete(sessionId);
    return record?.salt ?? null;
  }
}

export class SessionManager {
  constructor({
    redisUrl,
    ttlSeconds = DEFAULT_TTL_SECONDS,
    allowMemoryFallback = process.env.NODE_ENV !== 'production'
  } = {}) {
    this.ttlSeconds = ttlSeconds;
    this.allowMemoryFallback = allowMemoryFallback;
    this.memoryStore = new MemorySaltStore();
    this.redis = null;

    if (redisUrl) {
      this.redis = new Redis(redisUrl, {
        lazyConnect: true,
        maxRetriesPerRequest: 1,
        enableOfflineQueue: false,
        connectTimeout: 2500
      });
    }
  }

  async #ensureRedisConnection() {
    if (!this.redis) return false;
    if (this.redis.status === 'wait') {
      await this.redis.connect();
    }
    return this.redis.status === 'ready';
  }

  async createSession() {
    const sessionId = crypto.randomUUID();
    const salt = crypto.randomBytes(32).toString('hex');

    if (this.redis) {
      try {
        await this.#ensureRedisConnection();
        await this.redis.set(`cin:salt:${sessionId}`, salt, 'EX', this.ttlSeconds);
        return { sessionId, ttlSeconds: this.ttlSeconds, storage: 'redis' };
      } catch {
        if (!this.allowMemoryFallback) {
          throw new SessionStoreUnavailableError();
        }
      }
    }

    if (!this.allowMemoryFallback) {
      throw new SessionStoreUnavailableError();
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
        await this.#ensureRedisConnection();
        return await this.redis.call('GETDEL', `cin:salt:${sessionId}`);
      } catch {
        if (!this.allowMemoryFallback) {
          throw new SessionStoreUnavailableError();
        }
      }
    }

    if (!this.allowMemoryFallback) {
      throw new SessionStoreUnavailableError();
    }

    return this.memoryStore.consume(sessionId);
  }
}
