# Core Rules

Read for every generation or repair.

## Authority

Use this precedence:

1. Immutable SUT contract defines the provider's public behavior.
2. Immutable dependency contracts define downstream interactions.
3. Explicit requirements for behavior outside the contracts.
4. Compatible repository conventions.
5. Fresh executable evidence.

Never edit, normalize, regenerate, or repair a supplied specification. Fix application code, Specmatic configuration, or
additional examples while preserving supplied acceptance inputs. Report a contradiction as a blocker with concrete evidence.

Before declaring a defect or blocker, separate the observed failure from its hypothesized cause. State the evidence
supporting the hypothesis and run a bounded check that distinguishes it from plausible alternatives. Keep explanations
tentative until that check supports them; missing dependency interactions alone do not establish a contract contradiction.

Build the application components requested by the user. Derive whether a provider is a proxy, aggregator, orchestrator, or standalone service from
the supplied evidence; do not infer data models, workflows, or dependencies from operation names.

## Repository instructions

Before editing, read every applicable `AGENTS.md` and follow its instructions. Report concrete verification results
for required checks.

## Provider behavior

- Implement declared operations, inputs, outputs, security, content types, statuses, errors, and protocol metadata
  exactly.
- Preserve casing, missing/null distinctions, defaults, and validation constraints.
- Implement required state and side effects. Do not return canned successes.
- Never select behavior using `Specmatic-Response-Code`, call counts, global once flags, arbitrary identifiers, test
  order, or another test-only signal.
- Contract-valid inputs may drive explicit business rules and dependency requests. The real dependency/mock result must
  drive the provider outcome.
- Build outbound headers from a contract-derived allowlist; never forward every inbound header.

A contract test proves status and schema conformance, not arbitrary example values. Use response matchers from
[examples-and-matchers.md](examples-and-matchers.md) for application-level value relationships.

## Dependencies

Mock each supplied dependency with Specmatic unless the user requests a real service or the protocol cannot be mocked.
Read [dependency-mocking.md](dependency-mocking.md) for configuration, response control and interaction verification.

Dependency responses and examples must conform to their contracts. Verify required interactions from Specmatic-generated
reports. If a dependency is intentionally unused, explain the reason in the acceptance summary.

## Runtime and verification

### Scope quality commands before their first write

Before the first file-rewriting quality command, inspect its file selection and identify editable files, supplied
read-only inputs, and generated/runtime files using the current project's ownership rules.

Use the tool's supported include/exclude options or explicit editable paths. State the runnable command and its
covered/excluded paths; cover editable application code, tests and maintained documentation while preserving supplied
read-only inputs and excluding generated reports, caches and runtime-managed files. Persist this scope in project-local
commands. Preserve repository quality standards and record genuine baseline conflicts.

If ownership is unclear, use a non-writing check while resolving it; diagnostics do not authorize rewriting protected files.

- Use official Specmatic Enterprise artifacts and one checked-in root `specmatic.yaml` at version 3.
- Keep endpoints, ports, broker settings, imports, examples, and timeouts configurable as permitted by the brief.
- Set `specmatic.settings.test.schemaResiliencyTests: all`.
- Let Specmatic produce HTML and CTRF reports.
- Use `config validate` to diagnose configuration errors.
- When diagnosing readiness, use a declared health operation rather than a stateful or side-effecting business operation.
- Run repository-required formatter, lint, compile/type-check, unit, and build gates.
- Read production code before completion to check that no test-specific behavior control remains.

Read [specmatic-runtime.md](specmatic-runtime.md), the selected runtime guide, and
[acceptance-criteria.md](acceptance-criteria.md).
