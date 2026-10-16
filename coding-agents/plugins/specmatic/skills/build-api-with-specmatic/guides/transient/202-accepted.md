# 202 Accepted

When a mutating operation declares `202`, inspect its required headers and related monitor operations. A required `Link`
and monitor endpoint normally indicate asynchronous acceptance.

- Attempt the mapped downstream operation.
- On the specified transient condition, retain or queue the operation and return `202` only after it is accepted into
  workflow state.
- Return the contract-required monitor link, retry with the original idempotency key, and expose the actual terminal
  downstream result.
- Follow the URL or identifier returned by this interaction; an arbitrary or separately generated monitor ID is not
  evidence of the workflow.
- Do not convert permanent downstream rejection into `202` or replace downstream-owned domain state with provider
  workflow state.

An in-process queue or monitor store is acceptable for a self-contained sample when identified as sample-only and not
durable across process failure. If acceptance fails, return only a failure declared by the SUT contract; otherwise
report a contract gap.

Verify the accepted response and terminal monitor result in one correlated behavior with a bounded wait. Preserve the
declared link relation and URL shape. When the monitor ID exists only in a structured header, follow
[../behavior-fixtures.md](../behavior-fixtures.md). If an inline monitor example would generate an unrelated standalone
case, use its exact name for the correlated external example so it replaces rather than duplicates that case.
