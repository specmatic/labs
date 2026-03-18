# Lab: Test a MCP Server with Specmatic MCP Auto Test

## Objective
Run Specmatic MCP Auto Test against a real Streamable HTTP MCP server, observe two failing tool invocations, and fix the provider implementation without changing the dictionary or Docker Compose setup.

## Why this lab matters
MCP tools are often tested manually through ad hoc prompts or inspector utilities. That makes regressions easy to miss.

This lab shows the faster loop:
1. Keep the MCP server running locally.
2. Run automated MCP tool tests from a repeatable dictionary.
3. Use the failure output to fix the provider implementation.
4. Re-run until all tools pass.

## Time required to complete this lab
15-25 minutes.

## Prerequisites
- Docker is installed and running.
- You are in `labs/mcp-auto-test-python-service`.
- Port `8090` is available.

## Files in this lab
- `service/server.py`: MCP transport wiring and tool declarations.
- `service/order_service.py`: Backing business logic with two intentional bugs.
- `service/requirements.txt`: Python dependencies for the MCP server.
- `service/Dockerfile`: Builds the MCP server image.
- `dictionary/orders.json`: Input data used by MCP Auto Test.
- `docker-compose.yaml`: Starts the MCP server and the Specmatic MCP test runner.
- `build/reports/specmatic/mcp/`: Generated tools schema and JSON test report.

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
docker compose run --rm mcp-test \
  mcp test \
  --url=http://mcp-server:8090/mcp \
  --transport-kind=STREAMABLE_HTTP \
  --dictionary-file=dictionary/orders.json \
  --enable-resiliency-tests
```

This is not required for the lab goal. It is a follow-up to explore how Specmatic mutates valid tool inputs to probe validation boundaries.

## Pass criteria
- Baseline run fails with two tool execution failures.
- After fixing only `service/order_service.py`, both tests pass.
- `build/reports/specmatic/mcp/` contains generated output from the test run.

## Troubleshooting
- If the test runner starts before the server is ready, rerun after `docker compose down -v`.
- If code changes do not appear in the run, make sure you used `--build`.
- If port `8090` is busy, stop the conflicting process before running the lab.
- If Docker on Windows rewrites line endings, make sure edited Python files keep valid indentation.

## What you learned
- Specmatic can test Streamable HTTP MCP servers directly.
- MCP Auto Test uses tool schemas plus a dictionary file to generate repeatable invocations.
- Tool execution errors surface quickly when implementation behavior drifts from expected valid inputs.
