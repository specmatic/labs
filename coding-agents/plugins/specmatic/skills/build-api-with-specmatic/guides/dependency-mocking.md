# Dependency Mocking

Read whenever the provider has a downstream contract or a frontend/consumer needs a contract-driven mock. For
configuration generation and address fields, see [CLI commands](runtime/cli.md)
and [configuration v3](configuration-v3.md).

## Choose stateless or stateful behavior

Choose the mock mode from the consumer's expected behavior before starting it:

| Expected behavior                                                                      | OpenAPI run option    | What to verify                                                                                                                                                                                                                                       |
|----------------------------------------------------------------------------------------|-----------------------|------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| Independent responses, fixed examples, controlled errors, or request/response mapping  | `type: mock`          | For each request, the mock will return a contract-valid response based on a matching example or will dynamically generate one if no matching examples are provided. A successful POST does not imply that a later GET contains the created resource. |
| A resource lifecycle across requests, such as create then list/read, update, or delete | `type: stateful-mock` | Later requests observe the resource changes made by earlier requests in the same mock process.                                                                                                                                                       |

Specmatic supports both modes. For CRUD flows where later requests must observe earlier resource changes, choose a
stateful mock and verify the resulting resource state. Use deterministic expectations below for response scenarios;
finite/ordered transient expectations are a separate capability from resource state.

When generating configuration for a named OpenAPI dependency, use `--dependency-server-type=stateful`;
when adding one with `config update add-dependency`, use `--server-type=stateful`.
Both accept `stateless`, which is also the default when omitted.
See [CLI examples](runtime/cli.md#generate-specmaticyaml).
With MCP, set `serverType: "stateful"` on the dependency in `generate_config.dependencies`, or at the top level
of `add_dependency_to_config`; omission or `serverType: "stateless"` selects stateless behavior.
See the [MCP configuration example](runtime/mcp.md#configuration). If an older tool schema lacks this field,
set the dependency's OpenAPI run option to `type: stateful-mock` and call `validate_config` before starting the mock.

For direct MCP startup without a configuration, pass `serverType: "stateful"` to `start_mock_server` with
`contractPaths` and the chosen `port`. Omission or `"stateless"` selects stateless behavior. With `configPath`,
an explicit selector overrides the configured OpenAPI dependency types for the run; omit it to retain their configured
types. See [MCP startup](runtime/mcp.md#provider-and-mocks).

### Resource identity, seed data, and verification

- Stateful mocks use `id` as the resource identifier by default. For another field, the returned object schema uses
  `x-id-field`; for a collection, this is the array's item schema. Preserve supplied contracts: do not add extensions
  to an immutable specification merely to make a mock work.
- Eligible concrete GET/POST examples seed resources at startup. POST request and response fields can be combined
  into stored state, including APIs whose creation response contains only an ID. Examples with runtime matchers,
  substitutions, or templates are skipped as seeds. Validate examples and inspect actual starting state rather than
  assuming an empty collection or exact seed count.
- POST stores a resource, GET reads stored resources, PATCH/PUT update them, and DELETE removes them. These behaviors
  apply to operations declared in the contract. Resource bodies must be JSON objects; collection responses are arrays
  of objects. Query/path parameters filter resources when their names and types match resource fields.
- State lasts for the mock process and is isolated per specification. Restarting clears changes and reloads seeds.
  Independent scenarios should start from known state; do not rely on a previous run's resources.
- Verify all available CRUD operations supported by the contract using distinctive contract-valid resources and
  their actual identifiers. Where reads are available, confirm they reflect creation, updates, and deletion as
  applicable. Exercise declared filters as well. For a frontend task, verify supported flows through the UI with the
  real backend stopped and confirm state changes after fetching fresh data. Generated unrelated data or local
  optimistic updates alone do not prove mock persistence.
- If lifecycle behavior fails, inspect the effective run option, loaded contract/examples, resource identity and
  recorded requests before declaring stateful mocking unsupported. Report any contract/runtime incompatibility with
  evidence; do not silently weaken a required CRUD lifecycle check to independent response checks.

## Configure deterministic mocks

- Declare each dependency service and its mock run options in the root version 3 configuration. Give services separate
  configurable base URLs, hosts/ports, broker endpoints, or protocol addresses when needed.
    - Treat the first URL under the OpenAPI specification's `servers` section as an endpoint-shape hint, not as the
      mock's
      bind address. Preserve an explicit port and required base path when practical, but replace an environment-specific
      host with one reachable in the selected runtime: normally `localhost` for native execution, `0.0.0.0` for a
      container bind address, or the mock's service name for container-to-container calls. Keep the resulting `baseUrl`
      configurable and configure the provider to call that same reachable URL.
    - When the OpenAPI server URL has no explicit port, do not automatically bind the mock to inferred port 80 or 443.
      Select an available, configurable local mock port instead and preserve any required base path.
    - When available, extract the port from the host specified in the AsyncAPI spec under the servers section as the
      port
      for the mock.
- Keep examples scoped to their dependency specification. Confirm startup logs show the expected specifications and
  example counts; validation errors or missing examples are setup failures.
- Prefer persistent external expectations for stable scenarios. Use dynamic expectations only when a test must install
  runtime state, and transient expectations only for finite/ordered behavior.
- Expectation precedence is transient, dynamic, external, then inline. Design requests so the intended higher-priority
  expectation cannot accidentally shadow unrelated cases.
- Without a matching example, a non-strict mock may generate a contract-valid response. Use strict mock mode when every
  required interaction has a deterministic expectation and an unmatched request must fail; do not enable it when
  generated contract behavior is intentionally part of the test.
- Use literals before matchers. Make requests distinctive enough to avoid competing expectations, but use matchers for
  genuinely dynamic values.
- Use captures and substitution when a response must echo request data. Do not add an external response command when
  literals, matchers, captures, or a data lookup can express the behavior.
- Install a dynamic expectation through `POST /_specmatic/expectations` only when its values are unavailable before the
  test. Require a successful setup response before invoking the provider; Specmatic rejects expectations that do not
  conform to the dependency contract.
- Use example-specific delay for one scenario and configured global delay only when every response should be slow. Keep
  both bounded and deterministic.

Read [examples-and-matchers.md](examples-and-matchers.md) before writing or changing expectations. Read
[transient-expectations.md](transient-expectations.md) when an HTTP expectation must be served only a finite number of
times, optionally with delay.

### Provider examples that call mocks

Before choosing mock endpoints, inspect supplied `before`/`after` fixture URL templates. Set their existing template
variables in the Specmatic process environment so fixture calls and application downstream calls reach the configured
mocks; preserve supplied examples.

Inspect the provider's examples for `before` and `after` HTTP fixtures that call Specmatic mock control endpoints. These
fixtures may install expectations through `/_specmatic/expectations` or verify calls to dependency examples through
`/_specmatic/verify`.

Specmatic supplies these control endpoints, including the Kafka snapshot/verification API. If supplied `before`/`after`
snapshot or verification calls cannot connect, check that the relevant AsyncAPI dependency has `asyncapi.type: mock`
and that its Specmatic HTTP control API starts. Ascertain the configured broker endpoint and resolved fixture HTTP
control endpoint separately. Direct fixtures to that control API; do not create a relay, application dependency
contract,
or separate mock for Specmatic's own API.

For every such fixture, make its `baseUrl` resolve to the same reachable mock endpoint configured in `specmatic.yaml`.
Keep the value configurable when the execution environment can change, and preserve any required base path. Check the
resolved scheme, host, port, and path rather than assuming a contract server URL, fixture default, or hard-coded
`localhost` reaches the configured mock. In containerized runs, use the address reachable from the process executing the
fixture; this may differ from the mock's bind address and from the URL used by the provider.

## Start and observe mocks

Run the selected Enterprise runtime from the directory containing the root configuration. `run-suite` starts the
configured dependency mocks as part of acceptance; use the [runtime guides](specmatic-runtime.md) for execution and
application lifecycle details.

### Optional readiness checks

When managing mocks separately or diagnosing startup failures, check readiness using protocol-specific evidence:

- For HTTP, use `GET /actuator/health` and check that it reports `UP`.
- For messaging, confirm startup logs show that the configured contract loaded and the expected channels were
  discovered, then use the configured broker's readiness check.
- For other protocols, use the readiness check in the applicable protocol guide.

Run these checks from the same network context as the provider or fixture that will use the mock when containers or
separate network namespaces are involved. For a separately managed lifecycle, start dependencies before an application
that needs them during startup. These checks are optional troubleshooting tools; they are not an additional gate before
`run-suite` acceptance.

1. Use `--debug` when an expectation is not selected; confirm the file loaded, the outbound request matches the
   dependency contract, and the expected precedence applies.
2. Restart mocks between independent runs to reload known seeds; reset dynamic/transient expectations separately when
   used.
3. Stop only processes started by this workflow so usage reports are flushed.

## Verify HTTP interactions

Use `GET /_specmatic/messages` on the HTTP mock to inspect traffic served during the run. Filter with URL-encoded
equality selectors such as `REQUEST.PATH`, `REQUEST.METHOD`, `REQUEST.PARAMETERS.PATH.<name>`,
`REQUEST.PARAMETERS.QUERY.<name>`, `REQUEST.PARAMETERS.HEADER.<name>`, `REQUEST.BODY.<pointer>`, `RESPONSE.STATUS`,
`RESPONSE.HEADER.<name>`, and `RESPONSE.BODY.<pointer>`; multiple filters combine with AND semantics.

For every required derived mapping, verify that traffic reached the mock with the transformed request and that the
intended response/status was served. Absence of traffic is an implementation failure, not a reason to fabricate a
provider response.

Inspect Specmatic mock HTML/CTRF usage reports after shutdown. Treat `Covered` as observed matching traffic, `Not Used`
as an unexercised contract operation, `Missing In Spec` as observed undocumented traffic, and `Mismatch` as observed
traffic that did not conform. Explain intentional non-use; do not waive mismatches or missing-in-spec interactions.

Use [behavior fixtures](behavior-fixtures.md) to establish preconditions and verify interactions through mock control
APIs such as `/_specmatic/verify`. Diagnose unexpected results using recorded mock traffic alongside application logs.
