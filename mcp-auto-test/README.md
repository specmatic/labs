# Lab: Test MCP Servers with Specmatic MCP Auto Test

## Objective
MCP Auto Test addresses a critical gap in the MCP tool development lifecycle: automated, repeatable, and systematic testing of server-exposed MCP tools. This lab teaches you how to use Specmatic MCP Auto Test to validate a Streamable HTTP MCP server implementation, see tool execution failures, and fix the provider code until all tests pass.

## Why this lab matters
MCP tools are often tested manually through ad hoc prompts or inspector utilities. This approach makes it difficult to ensure consistent quality, slows down release cycles, and leaves room for regressions when new features are introduced.

MCP Auto Test addresses this gap by providing a reproducible, fully automated framework for schema drift Detection, regression, edge case, and input-combination testing of MCP tools exposed by an MCP Server. With automated coverage, teams can shift-left and catch issues earlier, improve reliability, and release changes with greater confidence.

This lab shows the faster loop:
1. Keep the MCP server running locally.
2. Run automated MCP tool tests from a repeatable dictionary.
3. Use the failure output to fix the provider implementation.
4. Re-run until all tools pass.

## Time required to complete this lab
15-25 minutes.

## Prerequisites
- Docker is installed and running.
- You are in `labs/mcp-auto-test`.
- Port `8090` is available.

## Files in this lab
- `service/server.py`: MCP transport wiring and tool declarations.
- `service/order_service.py`: Backing business logic with two intentional bugs.
- `service/requirements.txt`: Python dependencies for the MCP server.
- `service/Dockerfile`: Builds the MCP server image.
- `dictionary/orders.json`: Input data used by MCP Auto Test.
- `docker-compose.yaml`: Starts the MCP server and the Specmatic MCP test runner.
- `build/reports/specmatic/mcp/`: Generated tools schema, JSON test report, and HTML report.

## Who is who in this lab
- Test runner: Specmatic MCP Auto Test
- Provider: The local Python MCP server running on Streamable HTTP
- Backing implementation: `service/order_service.py`

## Learner task
Fix the two implementation bugs in `service/order_service.py` so both MCP tools pass automated testing.

## Lab Rules
- Do not edit `dictionary/orders.json`.
- Do not edit `docker-compose.yaml`.
- Do not edit `service/server.py`.
- Fix only `service/order_service.py`.

## Specmatic references
- MCP Auto Test: [https://docs.specmatic.io/getting_started/mcp_auto_test](https://docs.specmatic.io/getting_started/mcp_auto_test)
- MCP Auto Test dictionary and reports: [https://docs.specmatic.io/getting_started/mcp_auto_test#usage-guide](https://docs.specmatic.io/getting_started/mcp_auto_test#usage-guide)

## Part A: Baseline run (intentional failure)
Run:

```shell
docker compose up mcp-test --build --abort-on-container-exit
```

Expected result:
- Specmatic discovers both MCP tools from the local server.
- `get_order_summary` fails because the implementation looks up the wrong shipment field for order `ORD-2002`.
- `create_return_quote` fails because the implementation uses the wrong fee mapping key for reason `damaged`.

Expected summary:
```terminaloutput
Total: 2
Passed: 0
Failed: 2
```

What Specmatic is doing here:
- It reads the tool schemas exposed by the MCP server.
- It loads sample inputs from `dictionary/orders.json`.
- It invokes each tool and reports tool execution failures.

Artifacts created:
- `build/reports/specmatic/mcp/tools_schema.json`
- `build/reports/specmatic/mcp/mcp_test_report.json`
- `build/reports/specmatic/mcp/specmatic_report.html`

The HTML report is generated automatically as part of the `mcp-test` Docker Compose step.

Clean up:

```shell
docker compose down -v
```

## Part B: Fix the provider implementation
Open `service/order_service.py`.

Make these two fixes:
1. In `get_order_summary()`, use the existing shipment status field from the order record instead of the wrong key.
2. In `create_return_quote()`, fix the reason-to-fee lookup so the valid reason `damaged` works.

Do not change anything else.

## Part C: Re-run tests (expected to pass)
Run:

```shell
docker compose up mcp-test --build --abort-on-container-exit
```

Expected summary:
```terminaloutput
Total: 2
Passed: 2
Failed: 0
```

Clean up:

```shell
docker compose down -v
```

## Optional: Explore resiliency testing
After fixing the two bugs, run:

```shell
docker compose run --rm mcp-test --enable-resiliency-tests
```

This command still generates:
- `build/reports/specmatic/mcp/mcp_test_report.json`
- `build/reports/specmatic/mcp/tools_schema.json`
- `build/reports/specmatic/mcp/specmatic_report.html`

Expected Summary:
```terminaloutput
SUMMARY:
Total: 35
Passed: 33
Failed: 2
Overall Success Rate: 94.3%
```

This is not required for the lab goal. It is a follow-up to explore how Specmatic mutates valid tool inputs to probe validation boundaries. Try to pass all 35 tests.

## Pass criteria
- Baseline run fails with two tool execution failures.
- After fixing only `service/order_service.py`, both tests pass.
- `build/reports/specmatic/mcp/` contains generated output from the test run, including `specmatic_report.html`.

## Troubleshooting
- If the test runner starts before the server is ready, rerun after `docker compose down -v`.
- If code changes do not appear in the run, make sure you used `--build`.
- If port `8090` is busy, stop the conflicting process before running the lab.
- If Docker on Windows rewrites line endings, make sure edited Python files keep valid indentation.

## What you learned
- Specmatic can test Streamable HTTP MCP servers directly.
- MCP Auto Test uses tool schemas plus a dictionary file to generate repeatable invocations.
- Tool execution errors surface quickly when implementation behavior drifts from expected valid inputs.
