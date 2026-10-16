# Testcontainers

Require Docker for the Specmatic container; local Java is not required for Specmatic itself. Use the language's established Testcontainers support and framework-standard container setup. For image selection, configuration/report mounts and networking, follow [Docker CLI](docker-cli.md), adapting its Docker options to the Testcontainers API.

Mount the project containing `specmatic.yaml` and its contracts/examples, set the container working directory to that mount, and configure reachable provider and dependency endpoints. Mount report output writable and invoke `run-suite --agent`.

## Lifecycle

Start separately managed dependencies before an application that needs them during startup, then start the application before provider tests run. When `run-suite` manages the dependency mocks, it starts them as part of the suite; ensure application startup can complete before those mocks are available. For an application that requires live dependencies during startup, use a separately managed mock lifecycle with the selected runtime's supported commands.

Use Testcontainers-assigned host and mapped ports for callers outside the container network, and network aliases with container ports for callers inside it. Apply those addresses to the application, Specmatic configuration and fixture variables before the relevant process starts.

Follow the shared [licensing guidance](../specmatic-runtime.md#licensing) and the [Docker license mount/forwarding example](docker-cli.md#licensing-and-results). Capture container output and persisted reports, fail the test on a nonzero suite exit, and let the test lifecycle clean up its containers and application processes even when setup or acceptance fails.
