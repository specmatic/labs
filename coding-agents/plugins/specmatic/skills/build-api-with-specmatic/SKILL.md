---
name: build-api-with-specmatic
description: Use for contract testing and spec-driven mocking when implementing or updating a provider API from an API specification, or building a frontend against a Specmatic mock. Build the application, then use Specmatic Enterprise for controlled dependency mocks and acceptance tests.
---

# Build an API with Specmatic

## Workflow

Use available Specmatic [MCP tools](guides/runtime/mcp.md) for supported operations; otherwise use [Java CLI](guides/runtime/cli.md), then [Docker](guides/runtime/docker-cli.md). Read the selected runtime guide before configuring or running Specmatic.

When writing or changing a Java/Spring Boot application, consult the [Spring Boot guidance](guides/frameworks/spring-boot.md)
before implementing framework integrations, HTTP clients, or JSON serialization.

1. Implement from the supplied requirements, contracts and examples. Identify each specification's provider/dependency role from application interactions. Establish formatting and quality checks early; run relevant application tests.
2. Configure the provider and virtualize downstream dependencies with Specmatic. Adjacent `<spec-name>_examples` directories are auto-discovered; register only additional locations to avoid duplicate transient expectations. Run the complete suite to establish a baseline.
3. Fix failures and verify affected APIs using [filters](guides/runtime/cli.md#focused-diagnosis), including preconditions. Confirm selected tests executed and passed before complete acceptance, even for small or apparently final fixes. Broaden selection for wider effects; explain when filtered verification is unsuitable and use the smallest meaningful check.
4. Review against requirements and framework guidance, including behavior outside suite coverage. Resolve findings, add relevant regression coverage, and use step 3 for fixes covered by Specmatic. Finish formatting and required quality checks.
5. Remove filters and run complete final acceptance against the reviewed implementation. Failures return to step 3. Retain acceptance after test-only, documentation or formatting edits that leave application behavior and acceptance inputs unchanged; run checks relevant to those edits. Production code, runtime configuration, dependency or acceptance-input changes require fresh acceptance.

Preserve supplied contracts, examples, fixtures and assertions. Report the acceptance result and any unresolved failures honestly.

## Specmatic help

Consult references when the corresponding task arises:

- For new implementations or repairs, follow [core rules](guides/core-rules.md); use [generate](guides/generate-workflow.md) or [maintain](guides/maintain-workflow.md) guidance as applicable.
- When running final acceptance, verify complete suite results and provider/dependency CTRF reports: [acceptance criteria](guides/acceptance-criteria.md).
- Configure and run Specmatic through [MCP](guides/runtime/mcp.md) when available; use [CLI commands](guides/runtime/cli.md) for fallback and shared filter syntax.
- To reuse application startup and cleanup during CLI acceptance, optionally use the [minimal wrapper](guides/runtime/cli.md#optional-acceptance-wrapper).
- Configure service roles, ports, URLs, examples and settings: [configuration v3](guides/configuration-v3.md).
- Find the runtime and use existing licensing: [runtime](guides/specmatic-runtime.md). For other integration modes: [Docker CLI](guides/runtime/docker-cli.md), [native JVM](guides/runtime/native.md), [Testcontainers](guides/runtime/test-container.md).
- Mock an API for frontend development or control downstream responses and interactions: [dependency mocking](guides/dependency-mocking.md), [examples and matchers](guides/examples-and-matchers.md).
- When verifying asymmetric JWT signatures or testing authentication, preserve application trust keys and isolate test keys: [JWT verification and unit testing](guides/jwt-unit-testing.md).
- When writing or updating the application's README, document verified setup and acceptance commands: [README generation](guides/readme-generation.md).
- Set up preconditions or verify side effects: [behavior fixtures](guides/behavior-fixtures.md). For finite or delayed responses: [transient expectations](guides/transient-expectations.md).
- Protocol configuration: [REST](guides/protocols/rest.md), [Kafka](guides/protocols/kafka.md), [GraphQL](guides/protocols/graphql.md), [gRPC](guides/protocols/grpc.md), [SOAP](guides/protocols/soap.md).

Use the selected runtime's `--help`, reports and logs for details not covered here.

## Consumer and frontend mock flows

For frontend development and browser checks, read [frontend verification](guides/frontend-verification.md)
for installation readiness, server startup, selectors, and intentional error tests.

Before starting a mock for a frontend or other consumer, read [dependency mocking](guides/dependency-mocking.md)
and choose its mode from the required workflow. CRUD flows in which later requests must observe earlier resource
changes require stateful behavior. Configure `type: stateful-mock`; do not accept a tool's stateless default.
Verify all available CRUD operations supported by the contract. Where reads are available, confirm they reflect
creation, updates, and deletion as applicable. For UI work, verify the supported flows through the UI with the real
backend stopped and confirm state changes after fetching fresh data. Successful writes followed by unrelated
generated data are incomplete verification; passing the same flow against the real backend does not replace this gate.
