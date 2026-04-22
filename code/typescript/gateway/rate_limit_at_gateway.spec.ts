import { FixedWindowRateLimiter } from './rate_limit_at_gateway';

describe('FixedWindowRateLimiter', () => {
  it('should allow requests within limit', () => {
    const limiter = new FixedWindowRateLimiter(2, 1000); // 2 requests per second
    const now = 1000;

    const res1 = limiter.allow('user-1', now);
    expect(res1.allowed).toBe(true);
    expect(res1.remaining).toBe(1);

    const res2 = limiter.allow('user-1', now + 100);
    expect(res2.allowed).toBe(true);
    expect(res2.remaining).toBe(0);

    const res3 = limiter.allow('user-1', now + 200);
    expect(res3.allowed).toBe(false);
    expect(res3.retryAfterSeconds).toBe(1);
  });

  it('should reset window after time passes', () => {
    const limiter = new FixedWindowRateLimiter(1, 1000);
    const now = 1000;

    expect(limiter.allow('user-1', now).allowed).toBe(true);
    expect(limiter.allow('user-1', now + 100).allowed).toBe(false);

    // After 1 second (windowMs)
    expect(limiter.allow('user-1', now + 1001).allowed).toBe(true);
  });

  it('should track different clients independently', () => {
    const limiter = new FixedWindowRateLimiter(1, 1000);
    const now = 1000;

    expect(limiter.allow('user-1', now).allowed).toBe(true);
    expect(limiter.allow('user-2', now).allowed).toBe(true);
    
    expect(limiter.allow('user-1', now).allowed).toBe(false);
    expect(limiter.allow('user-2', now).allowed).toBe(false);
  });
});
