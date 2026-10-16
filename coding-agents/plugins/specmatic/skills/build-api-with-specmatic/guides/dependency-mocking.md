# Dependency Mocking

Read whenever the provider has a downstream contract. For configuration generation and address fields, see [CLI commands](runtime/cli.md) and [configuration v3](configuration-v3.md).

## Configure deterministic mocks

- Declare each dependency service and its mock run options in the root version 3 configuration. Give services separate
  configurable base URLs, hosts/ports, broker endpoints, or protocol addresses when needed.
  - Treat the first URL under the OpenAPI specification's `servers` section as an endpoint-shape hint, not as the mock's
    bind address. Preserve an explicit port and required base path when practical, but replace an environment-specific
    host with one reachable in the selected runtime: normally `localhost` for native execution, `0.0.0.0` for a
    container bind address, or the mock's service name for container-to-container calls. Keep the resulting `baseUrl`
    configurable and configure the provider to call that same reachable URL.
  - When the OpenAPI server URL has no explicit port, do not automatically bind the mock to inferred port 80 or 443.
    Select an available, configurable local mock port instead and preserve any required base path.
  - When available, extract the port from the host specified in the AsyncAPI spec under the servers section as the port
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
control endpoint separately. Direct fixtures to that control API; do not create a relay, application dependency contract,
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
2. Restart or explicitly clear stateful expectations between independent runs.
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
