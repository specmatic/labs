# Specmatic Configuration v3

Read when the selected runtime lacks `config generate`, when a protocol is unsupported by it, or when extending the
generated root `specmatic.yaml` with settings the command does not expose. For supported local OpenAPI SUTs and local
OpenAPI or Kafka AsyncAPI dependencies, prefer `config generate` and `config update add-dependency` over hand-written
YAML. Keep one contract-driven configuration containing only supplied specifications, selected protocols, and required
settings. Require `version: 3`.

## Shared model and wiring

Define reusable sources, services, and protocol-specific run options under `components`. Reference the provider from
`systemUnderTest.service` and each virtualized downstream service from `dependencies.services[].service`. `runOptions`
and service-scoped example `data` belong inside `service`.

```yaml
version: 3
systemUnderTest:
  service:
    $ref: "#/components/services/provider"
    runOptions:
      $ref: "#/components/runOptions/providerTest"
    data:
      examples:
        - directories: ["./examples/<additional-sut-example-directory>"]
dependencies:
  services:
    - service:
        $ref: "#/components/services/dependency"
        runOptions:
          $ref: "#/components/runOptions/dependencyMock"
        data:
          examples:
            - directories: ["./examples/<additional-dependency-example-directory>"]
components:
  sources:
    localContracts:
      filesystem:
        directory: .
  services:
    provider:
      definitions:
        - definition:
            source: { $ref: "#/components/sources/localContracts" }
            specs: [contracts/provider.yaml]
    dependency:
      definitions:
        - definition:
            source: { $ref: "#/components/sources/localContracts" }
            specs: [contracts/dependency.yaml]
  runOptions:
    # Replace these placeholders with fragments from the protocol guides.
    providerTest: {}
    dependencyMock: {}
```

Omit `dependencies` when none are supplied. Do not copy the empty run-option placeholders. Specmatic automatically
discovers `contracts/provider_examples` beside `contracts/provider.yaml` (and similarly for other specifications).
Use `service.data.examples[].directories` only for additional existing example locations. Replace the directory-name
placeholders above with those locations. Omit `data` when automatic discovery covers all examples; explicitly listing
the same directory can load a transient expectation twice.

Configure protocol-specific `runOptions` for the SUT and every configured dependency. Use `type: test` for
the SUT and `type: mock` for dependencies. Configure the connection fields required by the protocol: OpenAPI tests use
`baseUrl`, OpenAPI mocks use supported `baseUrl` addressing (including per-spec options) or `host` and `port`, AsyncAPI
uses a non-empty `servers` list, Protobuf and GraphQL SDL use `host` and `port`, and WSDL uses either `baseUrl` or `host`
plus `port`. Run the selected Enterprise artifact's `config validate` for URL validity and runtime-specific option rules.

## Sources and specification entries

Use exactly one source kind per source: `filesystem.directory`, `git.url`, or `web.url`. Specification paths are
relative to their source. Prefer scalar `specs` entries; use an object entry with stable `id` only for per-spec
endpoints, discovery, or credentials.

Never copy credentials into configuration. Use `{ENVIRONMENT_VARIABLE:defaultValue}`; resolution is environment
variable, then JVM system property, then default. Omit defaults for required secrets. Structured template values must
resolve to valid JSON objects or arrays.

Address examples use descriptive defaults such as `{PROVIDER_URL:<provider-url>}`. Replace angle-bracket placeholders
with the chosen environment values when creating the configuration; retain the substitution syntax for runtime overrides.

## Shared settings and reports

- Provider tests require `specmatic.settings.test.schemaResiliencyTests: all`.
- For focused diagnosis, pass MCP `run_test_suite.filter`, or use CLI `config update set-filter` in CLI mode. For final acceptance, omit the MCP filter and remove any saved CLI filter with `config update remove-filter`. See [shared filter syntax](runtime/cli.md#focused-diagnosis).
- Set `specmatic.settings.test.timeoutInMilliseconds` only when the default `6000` ms is inappropriate.
- Dependency-wide `startTimeoutInMilliseconds`, `delayInMilliseconds`, and `strictMode` belong under
  `dependencies.settings`. Use global delay only when every virtualized response should be delayed.
- Configure HTML and CTRF under `specmatic.governance.report`. Apply API coverage `successCriteria` only where coverage
  is supported.
- Keep CLI-only flags on the CLI. Do not add `openapi.strict` or `strict: true`; use documented dependency `strictMode`
  only when applicable.
- Add certificates, adapters, schema registry, workflow, or per-spec overrides only when required. Never store
  Enterprise license material here.
