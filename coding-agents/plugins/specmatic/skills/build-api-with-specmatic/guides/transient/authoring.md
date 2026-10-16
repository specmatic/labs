# Authoring Transient Expectations

Read [../examples-and-matchers.md](../examples-and-matchers.md) for base example and matcher semantics.

A transient expectation provides a contract-valid mock response for a finite number of matching requests, then becomes
unavailable so later requests can select another expectation or normal mock behavior. Correlate it with a distinctive
contract-valid request value, never execution order.

The expectation must:

- declare `"transient": true`;
- match the actual transformed downstream request;
- return a response declared by the dependency contract;
- use finite matcher counts when it must be served more than once; and
- allow the intended behavior after exhaustion.

Use `(uuid)` and `(string)` for unconstrained dynamic headers. Match fixed correlation values exactly. For generated
enum or boundary variants, use a named enum or validated primitive matcher with `value: each, times: 1`; when that
cannot preserve bounds, create literal expectations per value. Put query discriminators under `query` with `exact` and
finite `times`.

```json
{
  "transient": true,
  "http-request": {
    "method": "<METHOD>",
    "path": "<PATH>",
    "body": {
      "<CORRELATION_FIELD>": "<CONTRACT_VALID_VALUE>",
      "<ENUM_FIELD>": "$match(dataType: <NAMED_ENUM>, value: each, times: 1)"
    }
  },
  "http-response": { "status": "<DECLARED_STATUS>" }
}
```

Replace every placeholder. Keep object bodies as objects with field-level matchers. Do not manufacture an undeclared
dependency response.

## Optional delay

To delay each selected response, add top-level `"delay-in-milliseconds"` beside `"transient"`, `"http-request"`, and
`"http-response"`. Do not use `delay-in-seconds`, `delayInMilliseconds`, or place delay inside the response. A delayed
transient expectation models response latency, not DNS, TLS, connection refusal, or reset.

The delay may be a non-negative integer or a full-field Specmatic template with a non-negative integer default, such as
`"${TRANSIENT_RESPONSE_DELAY_MS:1500}"`. Any runtime override must also resolve to a non-negative integer. The timing
checker compares effective numeric values, so pass the delay selected for that run rather than the template expression.

When testing timeout-driven behavior, preserve applicable relationships:

```text
connection timeout > expected cold connection establishment
read timeout < transient delay
read timeout < transient delay < worker retry delay       # 202 recovery
read timeout < transient delay < Retry-After interval     # 429 recovery
```

Keep timing values configurable. Use the application's actual client and timeout configuration when diagnosing delayed responses; client-library timeout settings can cover different phases of an interaction.

## Orchestration

Use a supplied named SUT example or create a contract-valid external example without modifying the immutable contract.
Start the mock without consuming finite expectations, start the
provider against it, run the complete suite, inspect dependency traffic, reset state between isolated runs, and tear
down processes. When delay is used, do not freeze a sample `Retry-After` value into assertions; validate and use the
returned value.
