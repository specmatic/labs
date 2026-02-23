# Workflow Inside the Same Spec File

## Objective
In real API workflows, one call creates an ID and later calls must use that exact ID.  
This lab shows how Specmatic workflow mapping in `specmatic.yaml` propagates IDs from `POST /tasks` into `PUT /tasks/{task_id}` and `DELETE /tasks/{task_id}`.

Why this matters:
- Without workflow propagation, tests may still look green while exercising stale hardcoded IDs.
- With workflow propagation, your test flow behaves like production: create first, then update/delete the created entity.

## Time required to complete this lab
15-20 minutes.

## Prerequisites
- Docker Desktop (or Docker Engine) is installed and running.
- Docker Compose v2 is available (`docker compose version`).
- You are in `labs/workflow-in-same-spec`.

## Files in this lab
- `specmatic.yaml`: Workflow mapping (`extract` and `use`) configuration.
- `specs/tasks.yaml`: OpenAPI contract.
- `examples/*.json`: Externalized request/response examples.
- `docker-compose.yaml`: `mock` + `test` services for learner execution.

## Learner task
1. Intentionally break ID extraction in `specmatic.yaml`.
2. Run the lab and observe that requests stop using created IDs.
3. Fix the mapping and re-run to verify dynamic ID propagation.

## Lab Rules
- Edit only `specmatic.yaml`.
- Do not edit `specs/tasks.yaml`.
- Do not edit files in `examples/`.
- Use the exact command order in this README.
- Run cleanup after each execution:

```bash
docker compose down -v
```

## Intentional failure (Baseline run)
1. Open `specmatic.yaml`.
2. In `systemUnderTest -> service -> runOptions -> openapi -> workflow -> ids`, change:

```yaml
extract: "BODY.tasks.[0].id"
```

to:

```yaml
extract: "BODY.tasks.[0].taskId"
```

3. Run:

```bash
docker compose up test --abort-on-container-exit
```

4. In the test output, locate the `PUT /tasks/...` request lines.

Expected intentional failure signal:
- You will see `PUT /tasks/wf-put-input-201` (and similar `wf-put-input-*` values), which means the created ID was not propagated.
- The final test summary can still be green; this lab failure is behavioral (wrong workflow propagation), not only pass/fail count.

5. Clean up:

```bash
docker compose down -v
```

## Fix path
1. Reopen `specmatic.yaml`.
2. Restore:

```yaml
extract: "BODY.tasks.[0].id"
```

3. Re-run:

```bash
docker compose up test --abort-on-container-exit
```

4. Verify `PUT /tasks/...` lines now use a created value such as:
- `PUT /tasks/wf-created-plus-103`

5. Clean up:

```bash
docker compose down -v
```

## Pass criteria
- Workflow extraction line is `extract: "BODY.tasks.[0].id"` in `specmatic.yaml`.
- `PUT /tasks/...` requests in logs use a created ID (`wf-created-*`) instead of static `wf-put-input-*`.
- `DELETE /tasks/...` follows the propagated ID path.
- Final summary line is `Tests run: 14, Successes: 14, Failures: 0, Errors: 0`.

## Risks/gaps
- You may see warning `OAS0044` in output (from the provided OpenAPI schema). This warning does not block test execution in this lab.
- If Docker daemon is not running, `docker compose` will fail before the lab starts.
- Because external examples contain valid static IDs, purely checking green/red status is not enough; always verify request-path behavior in logs.

## Specmatic references (mapped to changes)
- Why request/response logs matter for contract tests: [Contract Testing](https://docs.specmatic.io/contract_driven_development/contract_testing.html)
- How externalized examples are loaded (this lab uses `examples/*.json`): [Externalized Examples](https://docs.specmatic.io/features/external_examples/)
- Understanding and triaging the warning shown in this lab output: [Rules - OAS0044](https://docs.specmatic.io/rules#oas0044)
