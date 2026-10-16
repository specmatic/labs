# Transient Mock Expectations

Read when a mock response must be served for a finite number of matching requests and then disappear from selection.
This finite lifetime is the core meaning of a transient expectation. A delay is optional.

Use transient expectations wherever a scenario needs temporary mock behavior, including one-time responses, finite
response sequences, delayed client responses, retry or recovery flows, and application behavior that may result in
`202`, `429`, or another contract-defined outcome.

Load only the applicable guidance:

- Read [transient/authoring.md](transient/authoring.md) to configure and orchestrate a finite expectation and any
  optional delay.
- If the resulting application behavior returns `202`, also read [transient/202-accepted.md](transient/202-accepted.md).
- If it returns `429`, also read [transient/429-too-many-requests.md](transient/429-too-many-requests.md).
- Only after selection, exhaustion, variant, or fallback behavior fails, read
  [transient/troubleshooting.md](transient/troubleshooting.md).

Derive provider behavior from the executable contracts, requirements, examples, and dependency mappings. Never select it
through a test-only control or test execution order.
