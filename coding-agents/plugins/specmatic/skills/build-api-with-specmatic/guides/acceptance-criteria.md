# Specmatic acceptance

Use the configured Specmatic environment to run acceptance against the final application, preserving supplied contracts,
examples, fixtures and assertions. Select behavior-specific checks from the brief, contracts and repository instructions.

## Acceptance result

- Run the complete, unfiltered Specmatic suite against the final implementation using the [selected runtime](specmatic-runtime.md). With MCP, call `run_test_suite` without `filter`; see [MCP](runtime/mcp.md). In CLI mode, use
  `java -jar "$SPECMATIC_JAR" run-suite --agent`; see [CLI commands](runtime/cli.md#run-acceptance).
  If only formatter changes follow a passing suite, retain that acceptance result without rerunning Specmatic.
- Confirm provider tests executed and passed. No discovered specifications, missing expected examples or zero executed
  tests indicate a setup problem.
- Confirm Specmatic generated CTRF reports for provider tests and each applicable dependency mock/stub, including
  messaging dependencies. See [dependency mocking](dependency-mocking.md#verify-http-interactions) for interpreting
  interaction evidence.
- Complete checks required by the brief or repository, including behavior and side effects that schema conformance alone
  cannot prove. See [dependency mocking](dependency-mocking.md#verify-http-interactions) and
  [behavior fixtures](behavior-fixtures.md) for interaction evidence.

Fix application or environment errors and finish with a passing complete, unfiltered suite. Report executed commands, observed
results, report locations and unresolved failures honestly. Preserve failure exit status and clean up processes you started.

For report configuration, see [configuration v3](configuration-v3.md#shared-settings-and-reports).
