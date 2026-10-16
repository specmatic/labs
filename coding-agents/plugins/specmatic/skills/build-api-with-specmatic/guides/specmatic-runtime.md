# Specmatic runtime and licensing

Prefer available [MCP tools](runtime/mcp.md) for supported operations, then [Java CLI](runtime/cli.md) when MCP is unavailable or lacks that operation, then [Docker](runtime/docker-cli.md) when host CLI execution is unavailable. Follow explicit project runtime requirements. A failed test, invalid configuration or licensing error needs diagnosis, rather than switching runtime to obtain a pass. Other integration modes: [native JVM](runtime/native.md), [Testcontainers](runtime/test-container.md).

Use the root version 3 `specmatic.yaml` for the provider and dependencies. Provider tests use `specmatic.settings.test.schemaResiliencyTests: all`. Test filters are useful for diagnosis; remove them for final acceptance. Strict provider test mode skips operations without examples, so use it only when that omission is intended.

Specmatic produces HTML and CTRF reports. No discovered specifications, missing expected examples, or zero executed tests indicate a setup problem rather than successful acceptance.

## Licensing

Use existing licensing inputs before requesting setup information:

1. Forward an existing `SPECMATIC_LICENSE_CONTENT` (license content) or `SPECMATIC_LICENSE_PATH` (path to a license file) without reading or logging its value.
2. Otherwise let host CLI/native execution use default license discovery under `~/.specmatic`; do not assume a filename.
3. For Docker/Testcontainers, forward the existing environment input or mount an existing `~/.specmatic` directory read-only at the runtime's home (the Enterprise CLI image uses `/root/.specmatic`). A path-based input must refer to a file accessible inside the container.

A CI secret named `SPECMATIC_LICENSE_KEY` can be mapped without logging to `SPECMATIC_LICENSE_CONTENT`, or to a protected file exposed through `SPECMATIC_LICENSE_PATH`. This is a CI secret naming convention, not an additional Specmatic runtime input.

Keep license contents out of source, images, logs and reports. Do not print or inspect license values, record user-specific absolute license paths in project documentation, or ask the user to paste license contents.

If the suite reports a licensing error, use `show-license` to debug it through the same artifact, environment and mounts as the failed suite. It is not a routine preflight step. Report non-sensitive setup options: `specmatic get-license`, `SPECMATIC_LICENSE_CONTENT`, `SPECMATIC_LICENSE_PATH`, or a custom container mount. Ask for a custom path only after existing inputs/default discovery fail and the user chooses path-based setup. After resolving the error, rerun acceptance; successful license diagnosis alone is not acceptance evidence.

## Further help

Prefer the selected runtime's help and local reports. Official documentation:

- https://docs.specmatic.io/references/configuration/getting-started
- https://docs.specmatic.io/references/configuration/test-configuration
- https://docs.specmatic.io/references/configuration/mock-configuration
- https://docs.specmatic.io/references/configuration/reports
- https://docs.specmatic.io/contract_driven_development/service_virtualization
- https://docs.specmatic.io/features/external_examples
- https://docs.specmatic.io/features/matchers
- https://docs.specmatic.io/features/testing_event_flows-and-behaviors
