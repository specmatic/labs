# External Examples and Matchers

Read when creating, updating, or diagnosing examples, or when tests must assert business values beyond the contract
schema.

## Keep test and mock semantics distinct

An external HTTP example contains `http-request` and `http-response`. Its role depends on where Specmatic uses it:

- In a provider contract test, the request supplies test data and the response status selects the expected scenario.
  Specmatic validates the live response against the contract. Plain response example values are not equality assertions;
  after contract validation succeeds, response `$match(...)` expressions provide API-level value checks.
- In service virtualization, Specmatic first validates an incoming request against the dependency contract, then uses
  request literals and matchers to select an expectation and serves its declared response.

Never confuse a SUT test example with a dependency expectation. Keep each under the service/specification it exercises,
and correlate them with distinctive contract-valid request values when one provider scenario requires a particular
downstream response.

For coordinated examples, trace the flow before diagnosing a mismatch:

1. Read the SUT example as the request sent to the provider and the provider outcome Specmatic will validate. Plain
   response values are not automatically the dependency's mock response or equality assertions.
2. Derive the exact outbound request the provider must send, including forwarded headers, query parameters, path values,
   and transformed body fields.
3. Match that outbound request against the dependency examples, expanding `partial`, captures, named patterns, and
   `data` substitutions.
4. Treat the selected dependency example's response as the downstream data the provider actually receives, then apply
   the brief's transformation and validation rules to determine the provider response.

Do not declare a contradiction by comparing a SUT example's plain response values directly with its request filters.
First prove which dependency example matches the forwarded request and what concrete response it produces. Values in the
headers, query or body fields may legitimately coordinate the two example sets; forwarding them is not test-specific
behavior.

Perform the investigation against the original supplied inputs; do not edit them during diagnosis. First check
application logic, configuration, test selection, prerequisites and runtime behaviour. Trace captures, substitutions
and matcher assertions before interpreting unexpected values as contradictions.

Ground the diagnosis in the failing test's request and response, application error details, and the dependency mock's
recorded request and response. Correlate evidence from the same execution. Where expectation selection or substitution
is disputed, establish which expectation matched and how captured values were resolved. If necessary evidence is
unavailable, identify and gather it before drawing a conclusion.

Until the necessary observations are available, describe the explanation as a hypothesis and name the missing
observation. Before declaring contradictory inputs, identify the exact requirements that cannot coexist and explain
why the intended asynchronous, retry or state-transition behavior cannot satisfy them. A failed implementation is
not evidence of contradictory requirements.

Question supplied inputs only when this reasoning exposes a concrete logical inconsistency. Establish exactly which
requirements cannot be satisfied together; unfamiliar syntax, unexpected results and repeated failures are insufficient
evidence.

Inline OpenAPI request and response examples with the same name form one test scenario and select its expected response
status. An external example keeps the request and response together in one JSON file. When no example selects a case,
Specmatic can still generate tests from the contract unless strict test mode intentionally excludes operations without
examples.

## Create and validate examples

Use the selected pinned Enterprise runtime to validate examples against their applicable contracts.

- Inventory and inspect every supplied inline and external example before creating fixtures. Reuse each applicable
  example as concrete guidance for request, response, message, scenario-trigger, and dependency-interaction data.
  Because contracts are immutable, add uncovered cases as external JSON rather than editing a supplied specification.
- By convention, an OpenAPI specification named `<name>.yaml` discovers files under `<name>_examples/` beside it. Do not
  also configure that same directory explicitly: it will be loaded twice and can produce duplicate or competing
  examples. Configure an examples directory only when it differs from the convention-based location.
- Include the request method/path and only applicable headers, query, form, multipart, and body fields. Include the
  expected response status; add response headers/body only for useful mock data or matcher assertions.
- A body may be an object, array, or string. Multipart entries use either `content` or an `@`-prefixed `filename`, never
  both.
- Preserve the contract's root JSON shape in request expectations. When the request schema is an object, keep `body` as
  an object and put matchers on its fields. Do not replace an object body with a whole-body matcher string such as
  `$match(contains: ...)`; matcher support at that location is runtime-version-dependent and an unsupported runtime
  validates it as a JSON string rather than an object.
- Validate examples non-interactively with the selected Enterprise runtime before starting tests or mocks. Treat failure
  as a hard stop. An invalid example may cause a mock to return contract-generated data instead.
- Treat competing requests as an error: if two examples match the same request but define different responses, selection
  is arbitrary. Do not use lenient competing-example detection merely to make validation pass.
- Use full external examples for documented `405` and `415` cases because the invalid method or media type cannot be
  represented as an inline OpenAPI request example. Keep the remaining request structure contract-relevant.
- A success example must be contract-valid. A documented `400` example may use the intentional contract-invalid input
  needed to trigger that response.
- To exercise an OpenAPI `default` response, use an external example containing the concrete undeclared HTTP status.
  `default` is not a status value and does not generate a test by itself.
- Do not use `[WIP]` examples to claim completion; they report failures without failing the build.

## Choose the narrowest matcher

Prefer a literal when the exact value matters. Otherwise use:

- `$match(exact: ...)` for deep equality of the complete scalar, object, or array. Extra object fields and
  reordered/extra array items fail.
- `$match(pattern: ...)` for a scalar regular expression.
- `$match(dataType: ...)` or a Specmatic pattern such as `(uuid)`, `(integer)`, or a contract-named pattern when only
  the valid shape matters.
- `$match(contains: ...)` for required object properties or array items while allowing unrelated content.

Put reusable operands under top-level `data` and reference them as `$(data.name)`. `exact` treats matcher-looking
strings inside referenced data as literals; `contains` recursively evaluates nested matchers in a referenced object.

For arrays, use `atLeast`, `atMost`, or `count` for matching-item cardinality; `atIndex`, `inFirst`, or `inLast` for
location/range; and `minLength`, `maxLength`, or `length` for total size. When `contains` references an array of matcher
items, each must match a distinct actual item; `contiguous` and `order` control adjacency and ordering. Do not combine
mutually exclusive parameters, and use `$match(length: 0)` for an empty array.

Capture a dynamic request value with `(NAME:type)` and reuse it as `$(NAME)` only when request/response correlation is
required. Keep capture names unique. Do not assume a named OpenAPI schema is available as a capture type in every
request location unless the selected runtime validates it there. For enum query/header values, use one literal
contract-valid example per enum value when primitive capture validation conflicts with the enum. Use captures primarily
for values whose primitive pattern is accepted in that location (for example UUIDs), and validate every example before
relying on response substitution.

When an external example is intended to supply or correlate with an existing named inline example, give it exactly the
same example name, including case. For a stateful monitor operation this can replace the unrelated generated inline case
with the correlated external behavior; a differently named example adds another independent test instead.

For an object request body, prefer field-level matchers that retain the schema shape. The following is only a structural
illustration; use field names, literal enum values, and patterns permitted by the contracts in the task:

```json
"body": {
"correlationKey": "transient-case",
"state": "$match(dataType: SchemaType, value: each, times: 1)",
"quantity": "$match(dataType: number, value: each, times: 1)"
}
```

`times` and `value: each|any` are valid only in transient mock examples. Follow
[transient/authoring.md](transient/authoring.md) for exhaustion rules.

Use a `partial` mock example only when unspecified required fields should still be validated from the contract and
generated by Specmatic. In strict mode, unresolved captures or data lookups are errors; without strict mode Specmatic
may generate a valid fallback value, so verify that substitution actually resolved when its value matters.

## Runtime values

Use example template values only for values that vary by environment. The form `${NAME|FALLBACK:default}` checks system
properties, then environment variables, from left to right and finally uses the mandatory default. Defaults must be safe
non-secret test values. Do not persist secrets in examples.
