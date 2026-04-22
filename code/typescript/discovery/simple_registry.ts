/**
 * Educational service registry / discovery demo.
 *
 * Goals:
 * - show how services can register themselves
 * - show health-aware discovery of instances
 * - keep the code minimal and easy to read
 *
 * Notes:
 * - this is not production code
 * - a real system would need heartbeats, TTL, health checks, retries, and persistence
 */

export type ServiceName = string;
export type InstanceId = string;

export interface ServiceInstance {
  id: InstanceId;
  host: string;
  port: number;
  healthy: boolean;
  zone?: string;
}

export class ServiceRegistry {
  private readonly services: Map<ServiceName, Map<InstanceId, ServiceInstance>>;

  constructor() {
    this.services = new Map();
  }

  public register(serviceName: ServiceName, instance: ServiceInstance): void {
    if (!this.services.has(serviceName)) {
      this.services.set(serviceName, new Map());
    }

    const instances = this.services.get(serviceName)!;
    instances.set(instance.id, instance);

    console.log(
      `[registry] registered service=${serviceName} instance=${instance.id} ` +
        `address=${instance.host}:${instance.port}`
    );
  }

  public deregister(serviceName: ServiceName, instanceId: InstanceId): void {
    const instances = this.services.get(serviceName);
    if (!instances) {
      return;
    }

    if (instances.delete(instanceId)) {
      console.log(
        `[registry] deregistered service=${serviceName} instance=${instanceId}`
      );
    }
  }

  public setHealth(
    serviceName: ServiceName,
    instanceId: InstanceId,
    healthy: boolean
  ): void {
    const instances = this.services.get(serviceName);
    if (!instances) {
      throw new Error(`unknown service: ${serviceName}`);
    }

    const instance = instances.get(instanceId);
    if (!instance) {
      throw new Error(`unknown instance: ${instanceId}`);
    }

    instance.healthy = healthy;

    console.log(
      `[registry] health updated service=${serviceName} instance=${instanceId} healthy=${healthy}`
    );
  }

  public discover(serviceName: ServiceName): ServiceInstance[] {
    const instances = this.services.get(serviceName);
    if (!instances) {
      return [];
    }

    return Array.from(instances.values()).filter((instance) => instance.healthy);
  }

  public chooseRoundRobin(serviceName: ServiceName, counter: { value: number }): ServiceInstance | null {
    const healthyInstances = this.discover(serviceName);

    if (healthyInstances.length === 0) {
      return null;
    }

    const index = counter.value % healthyInstances.length;
    counter.value += 1;

    return healthyInstances[index];
  }

  public snapshot(): Record<string, ServiceInstance[]> {
    const result: Record<string, ServiceInstance[]> = {};

    for (const [serviceName, instances] of this.services.entries()) {
      result[serviceName] = Array.from(instances.values());
    }

    return result;
  }
}

function demo(): void {
  const registry = new ServiceRegistry();
  const rrCounter = { value: 0 };

  registry.register("user-service", {
    id: "user-1",
    host: "10.0.0.1",
    port: 8080,
    healthy: true,
    zone: "eu-west-1a",
  });

  registry.register("user-service", {
    id: "user-2",
    host: "10.0.0.2",
    port: 8080,
    healthy: true,
    zone: "eu-west-1b",
  });

  registry.register("user-service", {
    id: "user-3",
    host: "10.0.0.3",
    port: 8080,
    healthy: false,
    zone: "eu-west-1c",
  });

  console.log();
  console.log("[client] healthy instances:", registry.discover("user-service"));

  console.log();
  console.log("[client] round robin choices:");
  for (let i = 0; i < 5; i++) {
    const chosen = registry.chooseRoundRobin("user-service", rrCounter);
    console.log(`request ${i.toString().padStart(2, "0")} ->`, chosen);
  }

  console.log();
  registry.setHealth("user-service", "user-2", false);

  console.log();
  console.log("[client] healthy instances after health change:");
  console.log(registry.discover("user-service"));

  console.log();
  console.log("[client] round robin choices after health change:");
  for (let i = 0; i < 4; i++) {
    const chosen = registry.chooseRoundRobin("user-service", rrCounter);
    console.log(`request ${i.toString().padStart(2, "0")} ->`, chosen);
  }
}

// demo();
