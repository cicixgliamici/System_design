/**
 * Educational in-memory API gateway rate limiter.
 *
 * Goals:
 * - show how a gateway could enforce per-client limits
 * - keep the implementation simple and readable
 * - connect theory with a concrete mechanism
 *
 * Notes:
 * - this is local/in-memory only
 * - a real distributed system would usually use Redis or another shared store
 * - window-based limiting is easy to explain, though token bucket is often better in production
 */

type ClientId = string;

interface RateLimitResult {
  allowed: boolean;
  remaining: number;
  retryAfterSeconds: number;
}

interface CounterState {
  count: number;
  windowStartMs: number;
}

export class FixedWindowRateLimiter {
  private readonly limit: number;
  private readonly windowMs: number;
  private readonly counters: Map<ClientId, CounterState>;

  constructor(limit: number, windowMs: number) {
    if (limit <= 0) {
      throw new Error("limit must be positive");
    }
    if (windowMs <= 0) {
      throw new Error("windowMs must be positive");
    }

    this.limit = limit;
    this.windowMs = windowMs;
    this.counters = new Map();
  }

  public allow(clientId: ClientId, nowMs: number = Date.now()): RateLimitResult {
    const state = this.counters.get(clientId);

    if (!state) {
      this.counters.set(clientId, {
        count: 1,
        windowStartMs: nowMs,
      });

      return {
        allowed: true,
        remaining: this.limit - 1,
        retryAfterSeconds: 0,
      };
    }

    const elapsedMs = nowMs - state.windowStartMs;

    if (elapsedMs >= this.windowMs) {
      this.counters.set(clientId, {
        count: 1,
        windowStartMs: nowMs,
      });

      return {
        allowed: true,
        remaining: this.limit - 1,
        retryAfterSeconds: 0,
      };
    }

    if (state.count < this.limit) {
      state.count += 1;

      return {
        allowed: true,
        remaining: this.limit - state.count,
        retryAfterSeconds: 0,
      };
    }

    const retryAfterMs = this.windowMs - elapsedMs;

    return {
      allowed: false,
      remaining: 0,
      retryAfterSeconds: Math.ceil(retryAfterMs / 1000),
    };
  }

  public snapshot(): Record<string, CounterState> {
    return Object.fromEntries(this.counters.entries());
  }
}

interface GatewayRequest {
  clientId: string;
  path: string;
  method: string;
}

export class ApiGateway {
  private readonly generalLimiter: FixedWindowRateLimiter;
  private readonly checkoutLimiter: FixedWindowRateLimiter;

  constructor() {
    // Example policies:
    // - general traffic: 5 requests per 10 seconds
    // - checkout endpoint: 2 requests per 10 seconds
    this.generalLimiter = new FixedWindowRateLimiter(5, 10_000);
    this.checkoutLimiter = new FixedWindowRateLimiter(2, 10_000);
  }

  public handle(request: GatewayRequest): void {
    const limiter =
      request.path === "/checkout" ? this.checkoutLimiter : this.generalLimiter;

    const result = limiter.allow(request.clientId);

    if (!result.allowed) {
      console.log(
        `[gateway] 429 Too Many Requests | client=${request.clientId} ` +
          `path=${request.path} retry_after=${result.retryAfterSeconds}s`
      );
      return;
    }

    console.log(
      `[gateway] 200 OK | client=${request.clientId} path=${request.path} ` +
        `remaining=${result.remaining}`
    );
  }
}

function demo(): void {
  const gateway = new ApiGateway();

  const requests: GatewayRequest[] = [
    { clientId: "user-1", path: "/catalog", method: "GET" },
    { clientId: "user-1", path: "/catalog", method: "GET" },
    { clientId: "user-1", path: "/catalog", method: "GET" },
    { clientId: "user-1", path: "/checkout", method: "POST" },
    { clientId: "user-1", path: "/checkout", method: "POST" },
    { clientId: "user-1", path: "/checkout", method: "POST" },
    { clientId: "user-2", path: "/catalog", method: "GET" },
  ];

  for (const request of requests) {
    gateway.handle(request);
  }
}

// demo();
