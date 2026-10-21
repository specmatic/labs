# Frontend verification

Use this guide when building or testing a frontend against Specmatic mocks and a real provider. Follow the
project's required build order and ports. Use the environment's browser tools and their interaction guidance.

## Installation and startup readiness

- Finish dependency installation successfully before starting the frontend. Existing `node_modules` can contain
  stale dependencies; a server starting from them does not prove the requested installation succeeded.
- If installation appears stalled, inspect its live process/session and output. Continue observing the same live
  operation while diagnosing it; do not launch a duplicate install. When a sandbox/network restriction is established,
  stop the stalled attempt and retry through the environment's approval mechanism. Follow its escalation rules.
- Start the intended dev-server mode and wait for its ready message and listening URL before browser navigation.
  Confirm the process remains live and the expected build owns the port. A port collision requires identifying its
  owner, not silently selecting another port or stopping an unrelated service.
- If navigation reports connection refused, check the startup session and listener before retrying. Do not treat a
  browser reload as a fix for a server that has not started.

## Mock and integration checks

Read [dependency mocking](dependency-mocking.md) to choose the mock mode and [MCP runtime](runtime/mcp.md)
for startup. For a create-and-list flow, use a stateful mock generated from the supplied contract.

1. Complete any required backend acceptance gate first. Then stop the real backend for the independent mock check.
2. Start the mock and frontend in mock mode. Confirm the frontend's effective API URL points to the mock.
3. Create a distinct entity through the UI. Confirm a subsequent list fetch displays its submitted fields; a
   successful creation message alone does not prove persistence. Check filtering when required by the project.
4. Stop the mock, switch the frontend to integration mode, and start the real provider. Confirm the effective API URL,
   then repeat creation and listing through the UI. Record the observed values and results for both modes separately.

If dependencies or application behavior change during these checks, repeat affected flows against the final build.
Mock success and real-provider success are separate requirements when the project asks for both.

## Browser interactions

Inspect the current rendered page before choosing selectors. Prefer role plus accessible name for controls,
for example a `combobox` named `Type`, scoped to the create form when needed to distinguish it from a filter.
Use label selectors when they resolve reliably and unambiguously.

After a selector timeout, inspect fresh page state and locator diagnostics before choosing another selector.
Do not repeat the same failing action blindly. Wait for an observable result, such as a matching list row or an
error message, instead of fixed sleeps. Distinguish an automation failure from an application failure in the report.

## Intentional error tests and cleanup

Announce deliberate failure tests before stopping a service or inducing an error so expected failures are recognizable.
Verify the visible error state, restore the service, and confirm the UI recovers through its normal retry or refresh
flow. Record intentional failures separately from unexpected errors.

Stop only processes and mocks started for this verification unless the user requests they remain running.
Report the verified startup commands or MCP payloads, tested modes, and any incomplete checks.
