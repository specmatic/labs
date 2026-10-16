# Maintain Workflow

## 1. Establish the baseline

Inspect working-tree status, applicable `AGENTS.md`, the root configuration, build files, project-local commands,
contract sources, supplied examples and current reports. Before invoking file-rewriting quality commands, complete
[the file-selection check](core-rules.md#scope-quality-commands-before-their-first-write), including any formatter embedded
in a test command. Run relevant existing tests when prerequisites are available and preserve repository quality coverage.

## 2. Make the smallest change

Re-resolve affected SUT and dependency contracts and inspect their examples. Follow [core rules](core-rules.md) and the
applicable references in [SKILL.md](../SKILL.md); revisit them when the change introduces a protocol, dependency or fixture.

Preserve compatible structure and integration mode. Change only provider behavior, adapters, configuration or additional
examples necessary to satisfy the contracts and request. Preserve supplied specifications and acceptance inputs. Use
focused quality or behavior tests when useful during development.

## 3. Update acceptance configuration

Configure the provider and dependencies in root `specmatic.yaml` using the [selected runtime](specmatic-runtime.md): MCP `generate_config` / `add_dependency_to_config` when available, otherwise [CLI configuration commands](runtime/cli.md#generate-specmaticyaml), then Docker. Use [configuration v3](configuration-v3.md) for settings the tools do not expose, including explicit Kafka server options. Validate configuration after edits.

Use [dependency mocking](dependency-mocking.md) to keep application, mock and fixture addresses aligned. Diagnose
configuration or example errors with validation commands and logs.

## 4. Verify and document

Follow [acceptance criteria](acceptance-criteria.md) against the final implementation. Update existing documentation using
[README generation](readme-generation.md) when setup or commands change.
