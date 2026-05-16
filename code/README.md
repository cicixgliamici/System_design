# Practical Code Implementations

This directory contains executable code examples that demonstrate the theoretical system design patterns covered in the repository.

We use a **polyglot** approach, choosing the language that best fits the paradigm or is most commonly associated with a specific component in the industry:

*   **Go (`/go`)**: Used for highly concurrent or performance-critical backend systems.
    *   Examples: Consistent Hashing, Worker Pools, Load Balancers.
*   **Python (`/python`)**: Used for scripting, quick prototyping, and data-centric algorithms.
    *   Examples: Caching strategies, Rate Limiters, Resilience patterns (Circuit Breaker).
*   **TypeScript (`/typescript`)**: Used for web-facing layers, API gateways, and ecosystem-specific patterns (like Node.js event loops).
    *   Examples: API Gateway, Service Registry.

## Running Tests

To ensure the reliability of the implementations, each module has its own test suite. You can run all tests across all languages using the unified `Makefile` in the root of the repository:

```bash
# Run tests for all languages
make test-all

# Or run tests for a specific language
make test-go
make test-python
make test-ts
```

For more details on a specific implementation, explore its directory and read the corresponding source code and test files.
