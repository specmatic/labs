# Specmatic Enterprise MCP

Use the registered `specmatic-enterprise` tools for supported operations. Discover their schemas, call `get_runtime_info` to identify the runtime, and use absolute project paths: the server may run from the plugin directory. If MCP is unavailable or a tool is absent, use Java CLI for that operation, then Docker if CLI is unavailable. Diagnose tool/configuration/license errors in the selected runtime; test failures are not a reason to switch.

When MCP supports the required operation, keep mock startup and verification in MCP. Do not run CLI or Docker
help commands merely to find an alternative to a working MCP operation. Investigate standalone commands when
the user requests them or an unsupported operation requires fallback. Document the verified MCP payloads when
those are the startup instructions actually used.

For application installation and dev-server readiness before browser checks, follow
[frontend verification](../frontend-verification.md). An MCP server running inside Docker still uses the MCP workflow;
distinguish that container runtime from invoking Specmatic through Docker CLI.

## Docker runtime in this lab

The lab plugin runs `specmatic/enterprise-snapshots:latest` with the lab directory recorded
during plugin installation mounted at the same absolute path. Start Codex from
`coding-agents/` using the README commands;
contracts, configurations and reports inside that directory are shared with the
container. The plugin forwards existing license inputs or the host's default
`~/.specmatic` directory. Docker is the selected runtime for this lab.

For the backend running on host port 3000, use
`http://host.docker.internal:3000` in Specmatic configuration. Container-local
`localhost` refers to the MCP container. The frontend still uses
`http://localhost:3000` in integration mode. Publish mock port 9001 through the
plugin's container and bind the mock to `0.0.0.0` so the host frontend can reach
`http://localhost:9001`. Use tool schemas to select the corresponding bind options.

## Configuration

Generate root `specmatic.yaml` with `generate_config`: pass `configPath`, `systemUnderTest` (specification path and base URL), and each dependency's name, specification path and optional base URL. Set `expectedConfigIdentity` to null for a new file; for updates use its current SHA-256 and `overwrite: true`. Later dependencies use `add_dependency_to_config` with the current hash. Use normal config edits for settings the tools do not expose, then call `validate_config`. Call `validate_all_examples` before acceptance. Adjacent example directories are auto-discovered; register only additional locations.

For OpenAPI dependencies, set optional `serverType` to `stateful` when later requests must observe earlier
resource changes, or `stateless` for independent responses. Omission defaults to stateless (`type: mock`);
`stateful` generates `type: stateful-mock`. In `generate_config`, put it inside each dependency:

```json
{
  "configPath": "/absolute/project/specmatic.yaml",
  "expectedConfigIdentity": null,
  "systemUnderTest": {"specificationPath": "provider.yaml", "baseUrl": "http://localhost:8080"},
  "dependencies": [
    {"name": "orders", "specificationPath": "orders.yaml", "baseUrl": "http://localhost:8090", "serverType": "stateful"}
  ]
}
```

For `add_dependency_to_config`, pass `serverType` alongside `name`, `specificationPath`, optional `baseUrl`,
`configPath` and the current `expectedConfigIdentity`. Repeating the same mode is idempotent; changing an
existing dependency's mode through this tool is a conflict, not an update.
For Kafka AsyncAPI, the same field accepts `in-memory` (default) or `external`, referring to broker type.
Values are validated against the specification protocol; HTTP mock modes and Kafka broker types are not interchangeable.
If an older server's tool schema lacks `serverType`, edit the dependency's OpenAPI run option and call `validate_config`.

## Provider and mocks

For consumer lifecycle flows, select stateful behavior before calling `start_mock_server`. Inspect the connected
tool's schema: use direct `contractPaths` with `serverType: "stateful"` when supported, or configure an OpenAPI
mock service with `type: stateful-mock` and start with `configPath`. Keep the real backend configured as the provider under
test and the consumer's mock service configured separately. Confirm the effective mode and verify persistence from
subsequent responses; tool startup success alone does not establish stateful behavior. If the available runtime cannot
support the required lifecycle, report the mock-flow gate as incomplete instead of substituting stateless checks.

Start the application yourself and confirm the intended build owns its listener. The MCP server must reach its URL and read its contracts, fixtures and configuration. `run_test_suite` starts and stops configured dependency mocks; avoid starting duplicate mocks. Stop the application after verification. For separately managed mocks use `start_mock_server`, `list_mock_servers`, `run_contract_test` and `stop_mock_server` as needed.

For direct OpenAPI startup, `start_mock_server` accepts optional `serverType: "stateful"` or `"stateless"`
(default). Use stateful mode for resource lifecycles such as create then list:

```json
{"mockId":"products-ui","contractPaths":["/absolute/project/products.yaml"],"port":9001,"serverType":"stateful"}
```

With `configPath`, an explicit `serverType` overrides the configured OpenAPI dependency mock types for that run
without rewriting the source config. Omit it to retain each service's configured type. Other direct inputs
(`contractPaths`, `port`, `exampleDirectories`) cannot be combined with config mode. Direct stateful mode requires local
OpenAPI files; Kafka broker types belong in configuration generation or dependency addition, not mock startup.
For older tool schemas without this selector, use a configuration with `type: stateful-mock` and start with `configPath`.

## Focused verification

Pass the same expression documented in [CLI filters](cli.md#focused-diagnosis) directly in `run_test_suite.filter`; no configuration edit is needed. For example:

```json
{"configPath":"/absolute/project/specmatic.yaml","filter":"METHOD='POST' && PATH='/resource' && STATUS='400'"}
```

For an API with a path parameter, use the contract template:

```json
{"configPath":"/absolute/project/specmatic.yaml","filter":"METHOD='GET' && PATH='/resource/{id}' && STATUS='404'"}
```

Include required preconditions and confirm the intended tests executed and passed. For complete final acceptance, omit `filter` and remove any diagnostic filter saved in configuration:

```json
{"configPath":"/absolute/project/specmatic.yaml"}
```

Inspect the actual structured tool result and its report inventory. Keep provider, HTTP mock and messaging reports distinct; confirm executed counts, failures and required interactions. MCP reports may be under `.specmatic-mcp/<run-id>` rather than the CLI report directory; use paths returned by the call. A successful tool invocation alone does not establish a passing suite. Apply the same [acceptance criteria](../acceptance-criteria.md) and project quality checks as other runtimes.
