# Specmatic Enterprise CLI

Use these commands when MCP is unavailable or lacks the operation; prefer available [MCP tools](mcp.md). Filter expressions below are shared by CLI and MCP.

Use the selected Enterprise JAR with Java 17+. Resolve `SPECMATIC_JAR` from the environment when supplied; otherwise the isolated runner provides `$HOME/.specmatic/specmatic-enterprise.jar`.

```bash
SPECMATIC_JAR="${SPECMATIC_JAR:-$HOME/.specmatic/specmatic-enterprise.jar}"
```

## Generate specmatic.yaml

Run from the application project root. Substitute the supplied contract files and the addresses chosen for this test environment:

```bash
java -jar "$SPECMATIC_JAR" config generate \
  --system-under-test=<provider-contract> \
  --system-under-test-url=<provider-url> \
  --dependency-name=<dependency-name> \
  --dependency-specification=<dependency-contract> \
  --dependency-base-url=<dependency-url>
```

Omit dependency options for a provider with no downstream contracts. Repeat a contiguous group beginning with `--dependency-name` for each dependency. This generates the root `specmatic.yaml`.

For each named OpenAPI dependency, `--dependency-server-type=stateful` generates `type: stateful-mock`.
Omitting this option or setting `--dependency-server-type=stateless` generates `type: mock`.
Choose based on the [required mock behavior](../dependency-mocking.md#choose-stateless-or-stateful-behavior):

```bash
java -jar "$SPECMATIC_JAR" config generate \
  --system-under-test=<provider-contract> --system-under-test-url=<provider-url> \
  --dependency-name=<dependency-name> --dependency-specification=<openapi-contract> \
  --dependency-base-url=<dependency-url> --dependency-server-type=stateful
```

`--dependency-server-type` is protocol-specific: OpenAPI accepts `stateful` or `stateless` (default);
Kafka AsyncAPI accepts `in-memory` (default) or `external`.
Kafka broker types do not select HTTP mock statefulness. `--dependency-server` and `--dependency-protocol`
remain Kafka AsyncAPI-only. Keep the type option within its dependency's contiguous named group.

For Kafka, the dependency group can specify a Specmatic-managed broker:

```bash
java -jar "$SPECMATIC_JAR" config generate \
  --system-under-test=<provider-contract> --system-under-test-url=<provider-url> \
  --dependency-name=<http-name> --dependency-specification=<http-contract> --dependency-base-url=<http-url> \
  --dependency-name=<kafka-name> --dependency-specification=<asyncapi-contract> \
  --dependency-server=<host:port> --dependency-protocol=kafka --dependency-server-type=in-memory
```

Use `external` instead of `in-memory` for an existing broker. Explicit AsyncAPI server options override declared server details; a specification without a server requires address, protocol and server type.

Add a dependency later with:

```bash
java -jar "$SPECMATIC_JAR" config update add-dependency --name=<name> --specification=<contract>
```

For OpenAPI, add `--server-type=stateful` for a stateful mock; omit it or use `--server-type=stateless`
for a stateless mock:

```bash
java -jar "$SPECMATIC_JAR" config update add-dependency \
  --name=<name> --specification=<openapi-contract> --base-url=<dependency-url> --server-type=stateful
```

For Kafka the add-dependency options are `--server=<host:port> --protocol=kafka --server-type=in-memory`.

Addresses and ports belong in the generated configuration's protocol-specific `components.runOptions`, referenced by each service. See [configuration v3](../configuration-v3.md) for the fields. See [dependency mocking](../dependency-mocking.md) for application and fixture wiring.

## Start a direct OpenAPI mock

For a standalone consumer or frontend mock without a configuration file:

```bash
java -jar "$SPECMATIC_JAR" mock <openapi-contract> --port=9001 --server-type=stateful
```

`--server-type` accepts `stateful` or `stateless`; omission defaults to stateless for direct startup.
Use stateful mode when later requests must observe created or updated resources. For v3 config-based startup, an explicit `--server-type` overrides the configured OpenAPI dependency mock types
for that run, preserving addresses and other settings without rewriting the source file. Omit it to retain each
service's configured `runOptions.openapi.type`. Existing `--host`, `--port` and `--data` options also apply to direct stateful mocks.
The CLI and MCP direct startup share the same implementation. Consult `mock --help` for runtime support;
older runtimes can use configuration-based stateful mocks instead.

## Run acceptance

Start the application using its project command and test-environment configuration. From the directory containing `specmatic.yaml`, run:

```bash
java -jar "$SPECMATIC_JAR" run-suite --agent
```

`run-suite` starts the configured dependency mocks and runs the provider tests. Use its output, reports, application logs and mock traffic to diagnose failures. Stop application processes you started when finished.

### Optional acceptance wrapper

To reuse application startup, suite invocation and cleanup, copy the [minimal Bash template](../../assets/templates/cli-test.sh.tmpl)
to a project-local `test.sh`. Run it from the directory containing `specmatic.yaml`:

```bash
APPLICATION_START_COMMAND='<foreground application launch command>' bash test.sh
```

Export application and fixture environment variables before invoking it. The wrapper inherits them, streams output,
returns the suite's exit status and stops the application process group it started. The launch command must stay in the
foreground and keep its children in that group. Build beforehand when the application requires it.

Before acceptance, confirm that the launched process is serving the intended build and owns the configured listening
port. A response from an older process does not establish readiness of the new build. Treat startup exit or a port-binding
failure as a failed launch; inspect and stop only processes owned by this workflow before retrying.

If application startup needs an explicit wait, optionally set `APPLICATION_READY_COMMAND` to a declared, side-effect-free readiness check and
`APPLICATION_START_TIMEOUT_SECONDS` to a suitable bound. No additional dependency readiness or license preflight is
required by the template. Use a declared health operation when available; otherwise use a safe startup/listener check
that verifies the launched process. No particular health path is assumed, and readiness does not require adding an endpoint.
Extra arguments go to `run-suite`, for example `bash test.sh --debug`.

Use the root configuration and supplied acceptance inputs. Remove diagnostic filters before final acceptance; the
wrapper does not decide whether the application is complete or validate report evidence.

## Useful commands

| Purpose | Command |
| --- | --- |
| Configuration validation | `java -jar "$SPECMATIC_JAR" config validate` |
| Example validation | `java -jar "$SPECMATIC_JAR" examples validate --specs-dir <dir> --examples-base-dir <dir> --examples-to-validate BOTH --competing-example-detection STRICT` |
| Runtime version | `java -jar "$SPECMATIC_JAR" --version` |
| License troubleshooting | `java -jar "$SPECMATIC_JAR" show-license` |
| Diagnostic output | `java -jar "$SPECMATIC_JAR" run-suite --debug` |
| Focus provider tests | `java -jar "$SPECMATIC_JAR" config update set-filter --system-under-test --filter=<expression>` |
| Restore all provider tests | `java -jar "$SPECMATIC_JAR" config update remove-filter --system-under-test` |

### Focused diagnosis

Use filters to select Specmatic scenarios when diagnosing suite failures or verifying fixes found during implementation review. Select contract attributes such as `METHOD`, `PATH`, `STATUS` or `EXAMPLE-NAME` from the failing report.

With MCP, pass the expression as the per-call `filter` on `run_test_suite` (see [MCP examples](mcp.md#focused-verification)); it leaves the configuration unchanged. The commands below are the CLI fallback.

For example, to reproduce invalid-input failures for `POST /resource`:

```sh
java -jar "$SPECMATIC_JAR" config update set-filter --system-under-test --filter="METHOD='POST' && PATH='/resource' && STATUS='400'"
java -jar "$SPECMATIC_JAR" run-suite
```

For an API with a path parameter, such as `GET /resource/{id}`, select the contract path template rather than a concrete request URL:

```sh
java -jar "$SPECMATIC_JAR" config update set-filter --system-under-test --filter="METHOD='GET' && PATH='/resource/{id}' && STATUS='404'"
java -jar "$SPECMATIC_JAR" run-suite
```

Replace the example attributes with those of the affected APIs. Include prerequisite operations for stateful scenarios in the selection, using `||` to include additional operations. Check the selected scenarios and report counts: a run selecting zero scenarios provides no verification. After a fix, verify the affected APIs with the filtered selection before complete acceptance, even when the fix appears small or final. Broaden the selection when other behavior is affected.

Once focused verification, implementation review and required quality checks pass, restore all provider tests and run final acceptance:

```sh
java -jar "$SPECMATIC_JAR" config update remove-filter --system-under-test
java -jar "$SPECMATIC_JAR" run-suite
```

Check the selected artifact's `config generate --help`, `config update add-dependency --help`, or other command help when an option is unavailable. For configuration not exposed by these commands, use [configuration v3](../configuration-v3.md).
