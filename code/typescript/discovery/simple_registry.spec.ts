import { ServiceRegistry } from './simple_registry';

describe('ServiceRegistry', () => {
  let registry: ServiceRegistry;

  beforeEach(() => {
    registry = new ServiceRegistry();
  });

  it('should register and discover healthy instances', () => {
    registry.register('test-service', {
      id: 'inst-1',
      host: 'localhost',
      port: 8080,
      healthy: true,
    });

    const instances = registry.discover('test-service');
    expect(instances).toHaveLength(1);
    expect(instances[0].id).toBe('inst-1');
  });

  it('should not discover unhealthy instances', () => {
    registry.register('test-service', {
      id: 'inst-1',
      host: 'localhost',
      port: 8080,
      healthy: false,
    });

    const instances = registry.discover('test-service');
    expect(instances).toHaveLength(0);
  });

  it('should handle health updates', () => {
    registry.register('test-service', {
      id: 'inst-1',
      host: 'localhost',
      port: 8080,
      healthy: true,
    });

    registry.setHealth('test-service', 'inst-1', false);
    expect(registry.discover('test-service')).toHaveLength(0);

    registry.setHealth('test-service', 'inst-1', true);
    expect(registry.discover('test-service')).toHaveLength(1);
  });

  it('should perform round robin selection', () => {
    registry.register('test-service', { id: '1', host: 'h1', port: 80, healthy: true });
    registry.register('test-service', { id: '2', host: 'h2', port: 80, healthy: true });

    const counter = { value: 0 };
    
    expect(registry.chooseRoundRobin('test-service', counter)?.id).toBe('1');
    expect(registry.chooseRoundRobin('test-service', counter)?.id).toBe('2');
    expect(registry.chooseRoundRobin('test-service', counter)?.id).toBe('1');
  });
});
