# Kafka / AsyncAPI

When the provider uses Spring Boot, also read [../frameworks/spring-boot.md](../frameworks/spring-boot.md) for
Jackson/Kafka serializer compatibility and broker-backed verification requirements.

Resolve servers, channels/topics, direction, key, headers, payload, examples, correlation/reply data, and
producer/consumer responsibility. Generate message-native handlers/clients and keep broker/topic configuration external.
For side-effect dependencies, publish at the contract-defined workflow point; do not invent request-response semantics.

Read [../behavior-fixtures.md](../behavior-fixtures.md) when behavior requires a trigger or observable side effect. Use
before/after fixtures and bounded waits to prove the flow rather than validating only message shape.

For every required to be produced message, verify all the following before calling the flow green:

- the producer receives broker acknowledgment or reports a bounded failure;
- the broker or Specmatic report contains at least one observed message;
- the actual serialized payload, key, and headers match the AsyncAPI schema;
- absent optional fields remain absent unless explicit `null` is allowed;
- no required message is missing and no observed message is invalid; and
- the triggering operation is correlated with the observed message rather than inferred from a synchronous API test
  alone.

Use the Kafka dependency reports to inspect observed messages and contract failures.

## Configuration v3

```yaml
# provider test
asyncapi:
  type: test
  replyTimeout: 10000
  subscriberReadinessWaitTimeout: 0
  servers:
    - host: "{BROKER_ENDPOINT:<broker-host:port>}"
      protocol: kafka

# dependency mock
asyncapi:
  type: mock
  servers:
    - host: "{BROKER_ENDPOINT:<broker-host:port>}"
      protocol: kafka
      type: in-memory
```

For an external broker, set `type: external`. Add admin, producer, consumer, and schema-registry settings only when
required by the contract and environment.
