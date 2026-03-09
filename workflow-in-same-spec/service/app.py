from flask import Flask, jsonify, request

app = Flask(__name__)

TASKS = {}
LAST_UPDATED_TASK_ID = None


@app.get("/actuator/health")
def health():
    return jsonify({"status": "UP"})


@app.post("/tasks")
def create_tasks():
    payload = request.get_json(force=True, silent=True) or {}
    content_type = request.headers.get("Content-Type", "")

    if content_type.startswith("application/*+json"):
        task_id = "wf-created-plus-103"
    elif content_type.startswith("text/json"):
        task_id = "wf-created-text-102"
    else:
        task_id = "wf-created-json-101"

    task = {
        "id": task_id,
        "type": "MANUAL_REVIEW",
        "category": "VERIFICATION",
        "subCategory": "IDENTITY",
        "state": "OPEN",
    }
    TASKS[task_id] = task

    return (
        jsonify(
            {
                "applicationNumber": payload.get("applicationNumber", "APP-1001"),
                "tasks": [task],
            }
        ),
        200,
    )


@app.get("/tasks")
def get_tasks():
    application_number = request.args.get("applicationNumber", "APP-1001")
    return (
        jsonify(
            {
                "applicationNumber": application_number,
                "tasks": [
                    {
                        "id": "wf-get-visible-401",
                        "type": "MANUAL_REVIEW",
                        "category": "VERIFICATION",
                        "subCategory": "IDENTITY",
                        "state": "OPEN",
                        "createdDate": "2026-02-20T00:00:00Z",
                    }
                ],
                "workflowState": "IN_PROGRESS",
            }
        ),
        200,
    )


@app.get("/tasks/<task_id>")
def get_task(task_id):
    task = TASKS.get(task_id) or {
        "id": task_id,
        "type": "MANUAL_REVIEW",
        "category": "VERIFICATION",
        "subCategory": "IDENTITY",
        "state": "OPEN",
    }
    task_response = {
        "id": task["id"],
        "type": task["type"],
        "category": task["category"],
        "subCategory": task["subCategory"],
        "state": task.get("state", "OPEN"),
        "createdDate": "2026-02-20T00:00:00Z",
        "updatedDate": "2026-02-20T00:10:00Z",
    }
    return jsonify(task_response), 200


@app.put("/tasks/<task_id>")
def update_task(task_id):
    global LAST_UPDATED_TASK_ID
    payload = request.get_json(force=True, silent=True) or {}

    if task_id not in TASKS:
        return jsonify({"message": "Task not found"}), 404

    updated_task = {
        "id": task_id,
        "type": "MANUAL_REVIEW",
        "category": "VERIFICATION",
        "subCategory": "IDENTITY",
        "state": "COMPLETED",
        "outcome": payload.get("outcome", "APPROVED"),
        "createdDate": "2026-02-20T00:00:00Z",
        "updatedDate": "2026-02-20T00:10:00Z",
    }
    TASKS[task_id] = updated_task
    LAST_UPDATED_TASK_ID = task_id
    return jsonify(updated_task), 200


@app.delete("/tasks/<task_id>")
def delete_task(task_id):
    if task_id not in TASKS:
        return jsonify({"title": "Not Found", "detail": "Task not found"}), 404

    TASKS.pop(task_id, None)
    return ("", 204)


@app.post("/tasks/verify")
def verify_tasks():
    verify_task_id = LAST_UPDATED_TASK_ID or "wf-verify-visible-503"
    payload = request.get_json(force=True, silent=True) or {}
    return (
        jsonify(
            {
                "applicationNumber": payload.get("applicationNumber", "APP-1001"),
                "tasks": [
                    {
                        "id": verify_task_id,
                        "type": "MANUAL_REVIEW",
                        "category": "VERIFICATION",
                        "subCategory": "IDENTITY",
                        "state": "COMPLETED",
                        "outcome": "APPROVED",
                        "createdDate": "2026-02-20T00:00:00Z",
                    }
                ],
                "workflowState": "VERIFIED",
            }
        ),
        200,
    )


@app.post("/tasks/cancel")
def cancel_tasks():
    return jsonify({"status": "CANCELLED"}), 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=9000)
