# Native Mode

Use only a verified official Enterprise-native package for selected language/protocol. If none exists, ask user to
choose cli, docker-cli, or test-container.

For JVM, use the project's selected `io.specmatic.enterprise:executable` test dependency and record its resolved
version. Contract test implements empty marker interface `io.specmatic.enterprise.SpecmaticContractTest`, adding
setup/teardown only when app lifecycle requires it. Do not declare OSS Specmatic modules directly, inspect JAR internals
for runners, or use legacy `io.specmatic.test.*` interfaces.

The project-local test command may be the framework-standard test command. For a self-contained lifecycle, start the SUT
before the marker test runs. For Spring Boot, use `@SpringBootTest` with the web environment required by the configured
SUT URL. Use an empty marker only when another test lifecycle demonstrably starts and stops the SUT.

## Resolve JVM dependency alignment

When configuring native tests, resolve the selected framework and Specmatic Enterprise test runtime together in a
minimal build. Inspect the resolved graph rather than maintaining a framework-to-Kafka version table.

For Maven, use a focused verbose tree such as:

    ./mvnw dependency:tree -Dverbose -Dincludes=org.apache.kafka

For Gradle, use dependency insight against the test runtime, for example:

    ./gradlew dependencyInsight --dependency kafka --configuration testRuntimeClasspath

When the sample uses Specmatic's in-memory Kafka broker:

1. Find the Kafka client and server artifacts requested by the selected Specmatic Enterprise async dependency.
2. Find the versions actually selected after framework dependency management.
3. If the framework replaced Specmatic's server line, align the generated sample to the Specmatic runtime's requested
   compatible line with the build tool's narrow dependency-management override.
4. Keep Kafka client, server, and test artifacts on a coherent compatible line; do not choose a version merely because
   it is latest.
5. Rerun the dependency report and start the in-memory broker once to prove the resolved graph contains the runtime
   classes it needs.

The generated sample should pin the derived compatible version for reproducibility. The skill must derive it again when
either the framework or Specmatic pin changes; do not encode a cross-version compatibility map here.

If the pinned Enterprise artifact itself fails dependency resolution, inspect the path to the failing coordinate.
Exclude only an optional component or a POM-only BOM from the Enterprise dependency edge when the graph proves that is
the cause. Revalidate a version-specific workaround when the Enterprise pin changes; do not add arbitrary replacement dependencies.

For license discovery and environment inputs, use the shared [runtime and licensing guidance](../specmatic-runtime.md#licensing) with the native test process's environment.
