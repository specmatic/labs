# Workflow Inside the Same Spec File

## Objective
Learn how Specmatic workflow mapping in `specmatic.yaml` propagates a created task ID from `POST /tasks` into `GET /tasks/{task_id}`, `PUT /tasks/{task_id}` and `DELETE /tasks/{task_id}`.

This lab uses a simple Python service with in-memory state, so missing workflow causes real contract test failures.

## Time required to complete this lab
15-20 minutes.

## Prerequisites
- Docker Desktop (or Docker Engine) is installed and running.
- Docker Compose v2 is available (`docker compose version`).
- You are in `labs/workflow-in-same-spec`.

## Files in this lab
- `specmatic.yaml`: Specmatic test configuration (starts with workflow intentionally missing).
- `specs/tasks.yaml`: OpenAPI contract.
- `examples/*.json`: Contract test examples.
- `service/app.py`: Python provider with in-memory task state.
- `docker-compose.yaml`: Runs `tasks-service` and `test`.

## Learner task
1. Run tests in the current baseline state (workflow missing).
2. Observe `PUT`/`DELETE` failures.
3. Add workflow mapping in `specmatic.yaml`.
4. Re-run and verify all tests pass.

## Lab Rules
- Edit only `workflow-in-same-spec/specmatic.yaml`.
- Do not edit `specs/tasks.yaml`.
- Do not edit files under `examples/`.
- Do not edit `service/app.py`.
- Use the exact command order below.

## Baseline run (intentional failure)
The `workflow` section is intentionally missing under:
`systemUnderTest -> service -> runOptions -> openapi`
(in `specmatic.yaml`, around line 21).

Run:

```bash
docker compose --profile test up test --build --abort-on-container-exit
```

Expected baseline result:

```text
Tests run: 15, Successes: 11, Failures: 4, Errors: 0
```

You should see failures for:
- `PUT /tasks/(task_id:string) -> 200` (3 scenarios)
- `DELETE /tasks/(task_id:string) -> 204` (1 scenario)

Why it fails:
- Without workflow, `PUT` and `DELETE` use static IDs from examples (`wf-put-input-*`, `wf-delete-input-*`).
- The in-memory provider only knows IDs created earlier by `POST /tasks` (`wf-created-*`).
- `examples/tasks_task_id_put_200*.json` validates response `id` using `$match(exact:wf-created-plus-103)`.

Cleanup:

```bash
docker compose --profile test down -v
```

## Fix path
Add this block in `specmatic.yaml` under `systemUnderTest.service.runOptions.openapi`:

```yaml
workflow:
  ids:
    "POST /tasks -> 200":
      extract: "BODY.tasks.[0].id"
    "GET /tasks/(task_id:string) -> 200":
      use: "PATH.task_id"
    "PUT /tasks/(task_id:string) -> 200":
      use: "PATH.task_id"
    "DELETE /tasks/(task_id:string) -> 204":
      use: "PATH.task_id"
```

Re-run:

```bash
docker compose --profile test up test --build --abort-on-container-exit
```

Expected passing result:

```text
Tests run: 15, Successes: 15, Failures: 0, Errors: 0
```

Cleanup:

```bash
docker compose --profile test down -v
```

## Troubleshooting
- If Docker is not running, compose commands fail before tests start.
- You may see warning `OAS0044`; it does not block this lab.
- If tests still fail after adding workflow, verify exact YAML indentation and scenario keys in `workflow.ids`.
