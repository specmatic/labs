# Generate Workflow

## 1. Resolve inputs

Reuse supplied values. Infer protocol/version from parsed content. Ask for missing essentials that cannot be determined
from the brief or repository: SUT contract, optional dependency contracts, stack, integration mode, and destination.

Resolve references/imports and inspect supplied inline and external examples. Identify operations/messages, inputs,
outputs, security, errors and dependency interactions. Read applicable `AGENTS.md` files and [core rules](core-rules.md).

## 2. Implement

Create the smallest genuine implementation using the normal development and testing process. Keep dependency endpoints
configurable as permitted by the brief and use explicit adapter boundaries. Derive responses from local state or real
downstream results; do not manufacture fixture-selected outcomes.

Before the first file-rewriting quality command, complete
[the file-selection check](core-rules.md#scope-quality-commands-before-their-first-write).

## 3. Configure acceptance

Configure the provider and dependencies in root `specmatic.yaml` using the [selected runtime](specmatic-runtime.md): MCP `generate_config` / `add_dependency_to_config` when available, otherwise [CLI configuration commands](runtime/cli.md#generate-specmaticyaml), then Docker. Use [configuration v3](configuration-v3.md) for settings the tools do not expose, including explicit Kafka server options. Validate configuration after edits.

Use [dependency mocking](dependency-mocking.md) to align application and fixture addresses with configured mocks and
control required responses. Diagnose configuration or example errors using the runtime's validation commands and logs.

## 4. Verify and document

Follow [acceptance criteria](acceptance-criteria.md) for complete acceptance and CTRF reports. Use
[README generation](readme-generation.md) when documenting verified setup and commands.
