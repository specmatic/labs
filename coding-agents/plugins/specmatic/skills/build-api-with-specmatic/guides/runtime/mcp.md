# Specmatic Enterprise MCP

Use the registered `specmatic-enterprise` tools for supported operations. Discover their schemas, call `get_runtime_info` to identify the runtime, and use absolute project paths: the server may run from the plugin directory. If MCP is unavailable or a tool is absent, use Java CLI for that operation, then Docker if CLI is unavailable. Diagnose tool/configuration/license errors in the selected runtime; test failures are not a reason to switch.

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

## Provider and mocks

Start the application yourself and confirm the intended build owns its listener. The MCP server must reach its URL and read its contracts, fixtures and configuration. `run_test_suite` starts and stops configured dependency mocks; avoid starting duplicate mocks. Stop the application after verification. For separately managed mocks use `start_mock_server`, `list_mock_servers`, `run_contract_test` and `stop_mock_server` as needed.

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
