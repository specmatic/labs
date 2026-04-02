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
- `specmatic.yaml`: Specmatic test configuration (starts with workflow intentionally missing).
- `.specmatic/repos/labs-contracts/openapi/workflow-in-same-spec/tasks.yaml`: OpenAPI contract loaded by `specmatic.yaml`.
- `examples/*.json`: Externalized request/response examples.
- `service/app.py`: Python provider with in-memory task state.
- `docker-compose.yaml`: Defines `tasks-service`, `test` (profile `test`) and `studio` (profile `studio`).

## Learner task
1. Run tests in the current baseline state (workflow missing).
2. Observe `GET`/`PUT`/`DELETE` failures.
3. Add workflow mapping in `specmatic.yaml`.
4. Re-run and verify all tests pass.

## Lab Rules
- Edit only `specmatic.yaml`.
- Do not edit the spec in `.specmatic/repos/labs-contracts/openapi/workflow-in-same-spec/tasks.yaml`.
- Do not edit files under `examples/`.
- Do not edit `service/app.py`.
- Use the exact command order below.

## Baseline run (intentional failure)
The `workflow` section is intentionally missing under:
`systemUnderTest -> service -> runOptions -> openapi`
(in `specmatic.yaml`).

Run:

```bash
docker compose --profile test up test --build --abort-on-container-exit
```

Expected baseline result:

```text
Tests run: 4, Successes: 1, Failures: 3, Errors: 0
```

You should see failures for:
- `GET /tasks/(task_id:string) -> 200` (1 scenario)
- `PUT /tasks/(task_id:string) -> 200` (1 scenario)
- `DELETE /tasks/(task_id:string) -> 204` (1 scenario)

Why it fails:
- Without workflow, `GET`, `PUT` and `DELETE` use random IDs from examples.
- The provider service only knows of IDs created earlier by `POST /tasks` (`wf-created-json-101`).
- `GET`, `PUT` and `DELETE` examples validate response `id` as the created task ID, so random IDs do not match.

Cleanup:

```bash
docker compose --profile test down -v
```

## Check in Studio
Run Studio with the provider service:

```bash
docker compose --profile studio up studio --build
```

Open Studio:
1. Open `http://127.0.0.1:9000/_specmatic/studio`,
2. Open `specmatic.yaml`, go to the `Test` tab, and run the suite. The contract is loaded into `.specmatic/repos/labs-contracts/openapi/workflow-in-same-spec/tasks.yaml`, which you can inspect from the left sidebar if needed.
3. You should see POST /tasks test pass, but GET/PUT/DELETE tests fail.
4. Look at the request/response details for the failed GET/PUT/DELETE tests and observe that we are not using the ID created by POST /tasks.

Stop Studio:

```bash
docker compose --profile studio down -v
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
Tests run: 4, Successes: 4, Failures: 0, Errors: 0
```

Cleanup:

```bash
docker compose --profile test down -v
```

## Next step
If you are doing this lab as part of an eLearning course, return to the eLearning site and continue with the next module.
