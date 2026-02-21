# Workflow inside Same Spec File

What if you want to create a resource using POST first and then use the created resource id for subsequent CRUD operations like GET, PUT, DELETE?

This lab demonstrates how you can use a built-in feature in Specmatic to define a lightweight workflow.

## Run mock + test with Docker Compose

```bash
docker compose up --abort-on-container-exit --exit-code-from test
```
## How does this work?
Open the [specmatic.yaml](specmatic.yaml) file and check the `workflow` section under `systemUnderTest/service/runOptions/openapi`

You will see the following:

```yaml
workflow:
  ids:
    "POST /tasks -> 200":
      extract: "BODY.tasks.[0].id"
    "PUT /tasks/(task_id:string) -> 200":
      use: "PATH.task_id"
    "DELETE /tasks/(task_id:string) -> 204":
      use: "PATH.task_id"
```

This informs Specmatic that when the test would create a list of tasks using the POST /tasks, pick the first id from the response and use that in subsequent requests like PUT /tasks/<task_id> or DELETE /tasks/<task_id> 