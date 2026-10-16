# REST / OpenAPI

Resolve every operation's method/path, parameters, headers, security, request and response media types, schemas,
examples, statuses, and external references. Generate contract-native routes and typed boundary models.

For each HTTP dependency mapping, derive the outbound method/path, request and response transformations, allowed
headers, credentials, timeout, status/error translation, and retry/idempotency behavior. Do not assume two OpenAPI
contracts share shapes or semantics.

Reject inputs that violate declared constraints and preserve the contract's missing, `null`, and default behavior. Do
not add an undocumented error response solely to make generated negative tests pass.

Deserialization is part of the HTTP contract boundary. Do not assume that a typed DTO plus bean validation preserves
JSON token types: many serializers coerce numbers or booleans into strings before validation runs. Add request-level
tests for incompatible JSON token types and verify the controller/service is not invoked. When the selected stack is
Spring Boot, read [../frameworks/spring-boot.md](../frameworks/spring-boot.md).

For OpenAPI providers, follow endpoint discovery, filtering, and coverage rules in
[../specmatic-runtime.md](../specmatic-runtime.md). Read [../transient-expectations.md](../transient-expectations.md)
when a mock response must expire after a finite number of matches. Read
[../behavior-fixtures.md](../behavior-fixtures.md) when an example needs setup, triggering, or side-effect verification
around its primary HTTP interaction.

## Configuration v3

```yaml
# provider test
openapi:
  type: test
  baseUrl: "{PROVIDER_URL:<provider-url>}"
  actuatorUrl: "{PROVIDER_URL:<provider-url>}/actuator/mappings"

# dependency mock
openapi:
  type: mock
  host: "{DEPENDENCY_HOST:<dependency-host>}"
  port: "{DEPENDENCY_PORT:<dependency-port>}"
```

Use `swaggerUrl` instead of `actuatorUrl` for discovery from a live OpenAPI document; they are mutually exclusive. Keep
filters diagnostic and remove them from the final suite. For per-spec credentials, use an object `specs` entry whose
`securitySchemes` key matches the OpenAPI scheme name. Supported types are `oauth2`, `openIdConnect`, `basicAuth`,
`bearer`, and `apiKey`. Use `workflow` only to extract a response value needed by a later request.
