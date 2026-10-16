# Spring Boot Boundaries

Read when the provider uses Spring Boot.

## Select Boot 4 modules deliberately

For Spring Boot 4, prefer Boot starters over bare integration libraries so the matching auto-configuration is present.
Use `spring-boot-starter-kafka` rather than adding only `spring-kafka`. Verify required beans with an application
context test; dependency presence alone does not prove that `KafkaTemplate` or `RestClient.Builder` was configured. If
the selected Boot 4 web modules do not provide a `RestClient.Builder`, construct `RestClient.builder()` explicitly and
apply the configured base URL and request factory/timeouts.

## Detect HTTP timeouts by cause

Do not classify a timeout solely by checking whether the top-level exception is `ResourceAccessException`. `RestClient`
may wrap it in another `RestClientException`. Walk the causal chain and recognize the concrete timeout types used by the
configured request factory, including `SocketTimeoutException` and `HttpTimeoutException`; keep non-timeout client
errors on their normal error path. Add adapter tests for the actual request factory used in production.

Reuse the production-configured client or factory bean in adapter regressions, with only the downstream address replaced
by a controlled server. A separately constructed default client can have different retry, timeout and serialization
behavior. For transport diagnosis, invoke the adapter directly first so retries by an HTTP test caller do not obscure
the adapter behavior; assert retry counts only when the task explicitly constrains them.

## Preserve JSON token types

Bean validation sees values only after Jackson has deserialized them. A numeric or boolean JSON token can therefore
become a nonblank Java `String` and pass annotations such as `@NotBlank`, contrary to an OpenAPI `type: string` schema.

Do not treat this property as strict string-token validation:

```yaml
spring:
  jackson:
    mapper:
      allow-coercion-of-scalars: false
```

Jackson's `ALLOW_COERCION_OF_SCALARS` governs non-textual scalar targets and does not reject number/boolean-to-`String`
conversion. `default-leniency: false` does not provide that guarantee either.

For Spring Boot 4 with its default Jackson 3 mapper, retain Boot's auto-configuration and add a
`JsonMapperBuilderCustomizer`:

```java
import org.springframework.boot.jackson.autoconfigure.JsonMapperBuilderCustomizer;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import tools.jackson.databind.cfg.CoercionAction;
import tools.jackson.databind.cfg.CoercionInputShape;
import tools.jackson.databind.type.LogicalType;

@Configuration
class StrictJsonConfiguration {
    @Bean
    JsonMapperBuilderCustomizer strictTextualJsonTokens() {
        return builder -> builder.withCoercionConfig(
                LogicalType.Textual,
                coercion -> coercion
                        .setCoercion(CoercionInputShape.Integer, CoercionAction.Fail)
                        .setCoercion(CoercionInputShape.Float, CoercionAction.Fail)
                        .setCoercion(CoercionInputShape.Boolean, CoercionAction.Fail));
    }
}
```

For Spring Boot 3/Jackson 2, apply the equivalent `CoercionConfig` to the Boot-managed `ObjectMapper`, using
`Jackson2ObjectMapperBuilderCustomizer` or a module/customizer supported by the selected Boot version. Do not replace
the Boot mapper wholesale unless necessary; doing so can discard registered modules and framework defaults.

If both Jackson 2 and Jackson 3 are present, determine which mapper the HTTP message converter actually uses before
configuring it. Avoid adding a second databind implementation casually; when both are required, explicitly configure the
preferred HTTP JSON mapper with the Spring Boot property supported by that version.

Add an HTTP-layer regression test for every affected token-shape boundary. At minimum, prove that a number and boolean
sent for an OpenAPI string property produce the contract's 4xx response and that business logic has no interaction. Run
the Specmatic acceptance suite with schema resiliency enabled; a mapper-unit test alone does not prove that the MVC converter
uses the customized mapper.

## Match the Kafka serializer to the Jackson generation

Spring Kafka 4 exposes serializers for both Jackson generations. Choose the serializer that matches the application's
mapper:

- Spring Boot 4 with its default Jackson 3 stack: use
  `org.springframework.kafka.support.serializer.JacksonJsonSerializer` (`tools.jackson.*`).
- Spring Boot 3/Jackson 2: use `org.springframework.kafka.support.serializer.JsonSerializer`
  (`com.fasterxml.jackson.*`).

For a default Spring Boot 4 application, configure the producer explicitly:

```yaml
spring:
  kafka:
    producer:
      value-serializer: org.springframework.kafka.support.serializer.JacksonJsonSerializer
```

Do not select the legacy `JsonSerializer` in a Jackson 3 application and then add
`com.fasterxml.jackson.core:jackson-databind` merely to make it load. Spring Kafka declares mapper dependencies as
optional, so a generation mismatch can survive compilation and application startup, then fail lazily on the first real
send with a linkage or serialization error. If publishing is in an HTTP request path, that error can surface as an
otherwise unexplained 500. For nonstandard or mixed dependency stacks, inspect the resolved dependency tree and the
serializer's mapper imports instead of inferring compatibility from the Spring Boot major version alone.

A serializer-construction test is insufficient because it need not serialize or send a value. Add a broker-backed
integration test that:

1. Starts the real test broker or Specmatic AsyncAPI mock and waits for readiness and topic creation.
2. Exercises the application endpoint or configured `KafkaTemplate` with a representative contract message.
3. Awaits the send result with a bounded timeout, or otherwise asserts the application's explicit asynchronous-failure
   handling.
4. Verifies that Specmatic observed a valid message for the expected AsyncAPI channel, with no missing or invalid
   interaction.

If successful publication is part of the HTTP operation's acceptance semantics, await the broker acknowledgment before
returning success. If it is intentionally asynchronous, make failures observable and test that recovery path. In either
case, include this verification in acceptance so a working HTTP stub cannot hide a broken Kafka side
effect.
