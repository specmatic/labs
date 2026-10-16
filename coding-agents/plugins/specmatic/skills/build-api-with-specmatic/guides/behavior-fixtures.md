# Before and After Behavior Fixtures

Read when an OpenAPI or AsyncAPI example must establish preconditions or verify side effects beyond the primary contract
interaction.

Use external examples with `before` and `after` fixture arrays:

- A `before` fixture stimulates a real boundary or establishes observable state before Specmatic executes the primary
  OpenAPI request or waits for the declared AsyncAPI `send` message.
- An `after` fixture observes a downstream call, state change, emitted event, or other public side effect after the
  primary OpenAPI interaction or AsyncAPI `receive` message.

Keep fixture requests and expected responses contract-valid. Use response matchers when an observation must assert
business values. Set bounded ISO-8601 `timeout` or `wait` values for eventual behavior instead of arbitrary sleeps.

For OpenAPI, keep the fixtures in the external example for the operation they surround. For AsyncAPI, place examples
under the configured examples root using the specification/operation directory convention required by the selected
runtime. Configure the exact directories in the root version 3 `specmatic.yaml`; do not copy obsolete configuration
shapes from tutorials.

Verify the complete behavior:

- every `before` fixture succeeds before the primary interaction;
- the primary HTTP operation or message matches its contract;
- every `after` fixture observes the required result within its bound;
- AsyncAPI payloads, headers, channel, and direction match the contract; and
- broker/mock state is reset between independent runs.

A passing schema check or primary HTTP status alone does not prove the behavior.

## Stateful follow-up operations

Do not execute a successful state-dependent lookup, status, or monitor operation as an isolated test with an arbitrary
generated identifier. Establish its state through the public operation that creates it, capture the identifier or URL
from that actual response, and use the captured value in the follow-up request.

For a `202` response with a monitor link, the behavioral test must:

1. trigger the real condition that makes the initiating operation return `202`;
2. capture the returned `Link` or monitor identifier rather than hard-coding an ID from an example;
3. derive the follow-up URL using the link semantics declared by the contract;
4. poll only that URL with a bounded timeout and contract-valid interval;
5. verify the recorded request and eventual downstream response; and
6. isolate or clear workflow state before the next scenario.

Use the selected Specmatic runtime's workflow support when it can extract and reuse the returned value. When the
identifier appears only inside a structured header and the runtime cannot transform it into a request path, use an
Arazzo workflow or a dedicated black-box behavior test that can parse the header. Do not seed an in-memory store, make
unknown IDs succeed, expose a test-only setup endpoint, or branch on a test-control header.

### Structured link correlation recipe

Do not assume a JSON-body workflow extractor can parse a structured header. First inspect the pinned artifact/config
schema for a supported header-to-path transformation. If none exists, implement the correlated behavior as a
project-level black-box test:

1. Send the initiating request and require the declared asynchronous status.
2. Read the actual structured link header as HTTP text.
3. Parse its target and parameters with an RFC-compatible link parser; for a single simple link, accept only the
   contract-declared pattern and extract the text between `<` and `>`.
4. Resolve a relative target against the provider base URL.
5. Poll only that resolved target, using the declared retry interval or a short bounded interval when none is declared.
6. Require the terminal response within an overall timeout and validate both intermediate and terminal responses against
   their specifications.
7. Record the initiating request, returned link, follow-up requests, and terminal result in one test report.

Fail immediately on a missing, malformed, cross-origin, or contract-invalid link. This test is the supported correlation
proof when the pinned Specmatic workflow cannot perform the structured-header transformation; a separate test using a
fabricated identifier is not equivalent.

If immutable OpenAPI examples cause the runtime to generate the successful follow-up operation independently and no
supported workflow can correlate it, report a contract/runtime modeling gap. Do not change correct provider behavior to
satisfy the isolated request or describe that isolated test as a valid monitor verification.
