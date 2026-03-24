---
name: specmatic-studio-workflow-authoring
description: Author and export Arazzo workflows in Specmatic Studio using the Workflow canvas. Use when the task involves clicking "Author a workflow", expanding OpenAPI or AsyncAPI specs in the Studio file tree, dragging method or action nodes into the canvas, connecting Start and End, generating the workflow, exporting an Arazzo spec, or debugging workflow-authoring behavior in Studio's web UI.
---
This repo contains labs that use Specmatic Studio's web UI. This skill is for the workflow canvas path specifically, not the Examples, Mock, or Test tabs.

# Specmatic Studio Workflow Authoring

Use this skill when the task is to create, inspect, export, or debug a workflow in Studio via `Author a workflow`.

## Quick Start

- Open Studio at `http://127.0.0.1:9000/_specmatic/studio`.
- Click `Author a workflow`.
- Open the left file explorer using `#left-sidebar-toggle`.
- Expand the tree until you reach the draggable method or action node.
- Drag the method or action node into the workflow canvas.
- Connect `Start` -> first step -> next step -> `End`.
- Click `Generate Workflow`.
- Click `Export Arazzo Spec`.
- Verify the exported `.arazzo.yaml` file on disk. Do not trust the UI alone.
- If the task includes executing the workflow, use Studio's workflow test flow and verify results step by step. Do not assume export success means runtime success.

## Browser Setup

- Prefer Playwright with Chromium already installed.
- Do not wait on `networkidle`. Studio keeps long-lived connections open.
- Prefer `domcontentloaded` plus explicit waits.
- Prefer `http://127.0.0.1:9000` over `localhost`.

## When Only Studio Is Needed

- For workflow drag-and-drop validation, start only Studio unless the task explicitly requires running the generated workflow.
- For export-only checks, Studio can write the Arazzo file without backend services running.
- For testing the generated Arazzo workflow, the dependent services must also be running.
- For the `arazzo-workflow-testing` lab, running the exported workflow also requires Kafka-backed async services, not just the OpenAPI services.

## Core Mental Model

The workflow explorer is a 4-level tree:

1. folder
2. spec file
3. operation or topic group
4. method or action node

Only level 4 is draggable.

Examples:

- OpenAPI:
  - `openapi`
  - `location.yaml`
  - `/location`
  - `getUserLocation`

- AsyncAPI:
  - `asyncapi`
  - `order.yaml`
  - `new-orders`
  - `createOrderSend`

Do not drag level 3 rows such as `/location`, `/products`, `new-orders`, or `accepted-orders`. They are grouping rows only.

## Reliable Tree Navigation

Use DOM-based Wunderbaum selectors.

Stable selectors:

- left sidebar toggle: `#left-sidebar-toggle`
- tree root: `#spec-tree`
- tree row: `#spec-tree .wb-node`
- tree expander within a row: `.wb-expander`

Common path selectors in this lab:

- openapi folder: `#spec-tree .wb-node[data-file-path="/usr/src/app/openapi"]`
- asyncapi folder: `#spec-tree .wb-node[data-file-path="/usr/src/app/asyncapi"]`
- location spec: `#spec-tree .wb-node[data-file-path="/usr/src/app/openapi/location.yaml"]`
- product spec: `#spec-tree .wb-node[data-file-path="/usr/src/app/openapi/product.yaml"]`
- warehouse spec: `#spec-tree .wb-node[data-file-path="/usr/src/app/openapi/warehouse.yaml"]`
- order openapi spec: `#spec-tree .wb-node[data-file-path="/usr/src/app/openapi/order.yaml"]`
- order asyncapi spec: `#spec-tree .wb-node[data-file-path="/usr/src/app/asyncapi/order.yaml"]`

Useful tree queries:

- operation rows: `#spec-tree .wb-node[data-type="operation"]`
- draggable rows: `#spec-tree .wb-node[draggable="true"]`

## Draggable Node Types

OpenAPI examples:

- `getUserLocation` with type `get`
- `getProducts` with type `get`
- `reserveInventory` with type `put`
- `getOrderDetails` with type `get`

AsyncAPI examples:

- `createOrderSend` with type `send`
- `createOrderReceive` with type `receive`
- `orderAccepted` with type `receive`
- `outForDelivery` with type `send`

In Studio's tree implementation, the row becomes draggable only when its parent row is an `operation` group.

## Workflow Canvas Model

The canvas starts with:

- `Start`
- `WorkflowId`
- `End`

The central workflow node is the effective drop target.

Observed drop target selector:

- `workflow-editor`
- shadow root selector for workflow node:
  `.svelte-flow__node.svelte-flow__node-workflow.draggable.connectable.selectable.nopan`

Do not target an assumed `parent` class unless you have verified it in the current build.

## Critical Export Rule

- The exported Arazzo only contains step nodes reachable from `Start` through the workflow edges.
- Dropping nodes onto the canvas is not enough. If a step is unconnected, it may be visible in the UI but missing from the exported YAML.
- Always validate that the graph is a single path from `Start` to `End` before generating.

## Authoring Flow

1. Open `Author a workflow`.
2. Optionally rename `WorkflowId`.
3. Expand the explorer tree to the method or action rows.
4. Drag each method or action row into the workflow node.
5. Confirm a step node appears after each drop.
6. Connect handles in sequence:
   - `Start` output -> first step input
   - each step output -> next step input
   - last step output -> `End` input
7. Click `Generate Workflow`.
8. Click `Export Arazzo Spec`.
9. Confirm the exported file exists and contains the expected steps.

## Handle Selectors

Observed handle patterns:

- Start source handle: `[data-id="1-Start-start-source"]`
- End target handle: `[data-id="1-End-end-target"]`
- step input handle: `[data-id="1-<step-id>-input-target"]`
- step output handle: `[data-id="1-<step-id>-output-source"]`

The `<step-id>` values are generated dynamically and should be discovered from the DOM after each drop.

## Recommended Validation After Each Drag

- Count the step nodes in the workflow shadow root:
  `.svelte-flow__node.svelte-flow__node-step`
- Keep the inserted step ids in workflow order rather than inferring order from visual layout.
- Visual layout can move nodes around after drop. Do not assume screen position equals logical order.

## Recommended Validation After Generate

- Inspect button state in the workflow editor shadow root.
- Confirm `Export Arazzo Spec` is present.
- Export the spec.
- Verify the file on disk using `find`, `ls`, or `sed`.
- Inspect the exported YAML for the full ordered step list. A successful export can still omit unconnected or misgenerated steps.

If export succeeds but the file contents are wrong, inspect the resulting YAML rather than trusting the canvas.

## Workflow Test Execution Model

When the task is to run the generated Arazzo through Studio, the backend flow is:

1. `POST /_specmatic/studio/workflow/test`
2. capture the returned event id
3. `POST /_specmatic/studio/task/start` with that id
4. poll `POST /_specmatic/studio/workflow/{eventId}` for each workflow step

Important runtime rules:

- Preserve the same Studio session cookie across all these requests.
- Calling `/workflow/test` alone only registers the task. The run does not actually start until `/task/start`.
- If polling returns empty or stale results, suspect lost session state before suspecting the workflow itself.
- For UI-driven runs, the Studio frontend handles this. For direct HTTP debugging, you must do it yourself.

## Lab-Specific Tree Map For `arazzo-workflow-testing`

Expected authoring sequence for the lab:

1. `getUserLocation`
   - folder: `openapi`
   - spec: `location.yaml`
   - group: `/location`

2. `getProducts`
   - folder: `openapi`
   - spec: `product.yaml`
   - group: `/products`

3. `createOrderSend`
   - folder: `asyncapi`
   - spec: `order.yaml`
   - group: `new-orders`

4. `createOrderReceive`
   - folder: `asyncapi`
   - spec: `order.yaml`
   - group: `wip-orders`

5. `reserveInventory`
   - folder: `openapi`
   - spec: `warehouse.yaml`
   - group: `/inventory`

6. `orderAccepted`
   - folder: `asyncapi`
   - spec: `order.yaml`
   - group: `accepted-orders`

7. `outForDelivery`
   - folder: `asyncapi`
   - spec: `order.yaml`
   - group: `out-for-delivery-orders`

8. `getOrderDetails`
   - folder: `openapi`
   - spec: `order.yaml`
   - group: `/orders/{orderId}`

## Lab-Specific Runtime Notes For `arazzo-workflow-testing`

- The expected runtime path is:
  `getUserLocation` -> `getProducts` -> `createOrderSend` -> `createOrderReceive` -> `reserveInventory` -> `orderAccepted` -> `outForDelivery` -> `getOrderDetails`
- The branch `getProducts.IsArrayEmpty` is an input-assert case and should skip downstream order-placement steps.
- Studio may generate placeholder values in `PlaceOrder.arazzo_input.json`. For this lab, overwrite them with:
  - `DEFAULT.getUserLocation.userEmail = blr@specmatic.io`
  - `getProducts.IsArrayEmpty.getUserLocation.userEmail = del@specmatic.io`
  - `DEFAULT.createOrderSend.requestId` set to a stable value such as `123e4567-e89b-12d3-a456-426614174000`
- A successful full run in this lab produces 11 successful results:
  - 2 for `getUserLocation`
  - 3 for `getProducts`
  - 1 each for `createOrderSend`, `createOrderReceive`, `reserveInventory`, `orderAccepted`, `outForDelivery`, `getOrderDetails`
- If `createOrderReceive` times out while `createOrderSend` succeeds, inspect the async step metadata first.
- On a cold start, the first workflow test run may fail at `createOrderReceive` due to async consumer or topic warm-up, even when the exported workflow is correct.
- If `createOrderSend` succeeds, the order service logs show `Published ORDER WIP EVENT`, and `createOrderReceive` still times out on the first run, rerun the workflow once before concluding the spec is wrong.

## Async Step Metadata Matters

For AsyncAPI steps, the generated/exported workflow needs the correct `operationId` and action pairing. In this lab the working mappings are:

- `createOrderSend`
  - `operationId: "$sourceDescriptions.AsyncOrderApi.createOrder"`
  - `action: "send"`
- `createOrderReceive`
  - `operationId: "$sourceDescriptions.AsyncOrderApi.createOrder"`
  - `action: "receive"`
- `orderAccepted`
  - `operationId: "$sourceDescriptions.AsyncOrderApi.orderAccepted"`
  - `action: "receive"`
- `outForDelivery`
  - `operationId: "$sourceDescriptions.AsyncOrderApi.outForDelivery"`
  - `action: "send"`

If a hand-built or partially generated workflow uses the wrong async mapping, Studio may export a valid-looking file that fails at runtime.

## Known Pitfalls

- The method or action node is draggable. The operation or topic row is not.
- `createOrderReceive` is under `wip-orders`, not `new-orders`.
- The workflow node class may not include `parent` in the current build.
- Export only includes steps reachable from `Start`.
- Export can succeed even if the generated workflow is incomplete.
- If the workflow name edit does not persist, Studio may export `WorkflowId.arazzo.yaml` instead of the intended name.
- A generated file on disk is not enough. Inspect the YAML to confirm all expected steps are present.
- When automating, connection order should follow insertion order, not node position on screen.
- For direct HTTP testing, forgetting `/task/start` or losing the Studio session cookie will make workflow polling look broken.
- Async failures after a successful send often indicate wrong action or `operationId` metadata, not an infrastructure problem.
- On a fresh stack boot, the first async receive test can fail because the subscriber is not fully ready yet. Treat a first-run `wip-orders` timeout as potentially transient.
- Do not trust Studio-generated random input values for this lab. Replace them with the known-good emails and a stable `requestId` before diagnosing workflow failures.

## What To Inspect When Export Looks Wrong

- exported YAML file contents
- generated input JSON file contents
- presence of all expected step ids before generate
- presence of `Export Arazzo Spec` button after generate
- whether the workflow name changed from `WorkflowId`
- whether every expected step is reachable from `Start` in the canvas graph
- whether async steps have the expected `operationId` and `action` pairs

Files often written by Studio:

- `*.arazzo.yaml`
- `*.arazzo_input.json`

## Automation Tips

- Use DOM-dispatched clicks for tree expanders when visible clicks are flaky.
- Use mouse-based drag and drop for workflow insertion.
- Prefer reading the workflow editor shadow root directly for nodes and buttons.
- Keep explicit waits between expand, drag, connect, generate, and export actions.
- After each drop, compare the step-id set before and after to capture the newly inserted step id.
- If drag-and-drop automation is flaky, compare the exported YAML against the intended step list before trying to debug runtime failures.
- For backend verification, direct HTTP calls to Studio are useful, but preserve cookies and call `/task/start`.

## Verification Commands

Examples:

- `find /path/to/specs -maxdepth 2 -type f | sort`
- `ls -l /path/to/specs/*.arazzo.yaml`
- `sed -n '1,160p' /path/to/specs/WorkflowId.arazzo.yaml`
- `rg -n "workflowId:|steps:|operationId:|action:" /path/to/specs/PlaceOrder.arazzo.yaml`

## Scope Boundary

Use this skill for workflow canvas authoring and Arazzo export behavior.

If the task is instead about:

- opening a normal spec
- generating examples
- starting mocks
- running contract tests

use `specmatic-studio-navigation` instead, or use both skills together if the task spans both areas.
