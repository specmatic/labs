# API Workflow Testing using Arazzo

Want to test the functionality of an entire business workflow of your microservices architecture that involves both synchronous HTTP calls and asynchronous event-driven interactions?

![Order Application Workflow](assets/arazzo-workflow.gif)

Using a simple drag-and-drop approach, Specmatic-Arazzo facilitates generating an entire workflow and exporting it as an industry-standard Arazzo specification. Once you've created the Arazzo specification, you can leverage Specmatic-Arazzo to perform end-to-end workflow testing and mocking for your microservices architecture.

More details: https://docs.specmatic.io/supported_protocols/arazzo

## Sequence Diagram

![Sequence Diagram](./assets/arazzo-flow.svg)

## Time required to complete this lab:
10-15 minutes.

## Prerequisites
- Docker is installed and running.
- You are in `labs/arazzo-workflow-testing`.

## API Workflow Testing Overview Video
[![Watch the video](https://img.youtube.com/vi/baYcsznD_Mk/hqdefault.jpg)](https://www.youtube.com/watch?v=baYcsznD_Mk)

## Getting Started

Start the full stack using Docker Compose:

```shell
docker compose up --build
```

This launches the following services:

| Service           | Port | Description                    |
|-------------------|------|--------------------------------|
| **Location API**  | 3000 | Provides user location details |
| **Products API**  | 3001 | Returns products by location   |
| **Order API**     | 3002 | Handles order lifecycle        |
| **Warehouse API** | 3003 | Manages inventory operations   |
| **Kafka**         | 9092 | Internal broker port           |
| **Postgres**      | 5432 | Shared database                |

Start Studio
```shell
docker run --rm --network host -v ./specs:/usr/src/app specmatic/enterprise studio
```

Open [http://127.0.0.1:9000/_specmatic/studio](http://127.0.0.1:9000/_specmatic/studio).

Then:
1. Click on `Author a workflow` button.
2. Click on `WorkflowId` and give a name to your workflow like `PlaceOrder`.
3. Click on the `>>` chevron icon to open the file explorer
4. From the specs in the file explorer, drag and drop the following specs into the workflow canvas in this order:
   - `getUserLocation` from `openapi/get_location.yaml`
   - `getProducts` from `openapi/get_products.yaml`
   - `createOrderSend` from `asyncapi/order.yaml`
   - `createOrderReceive` from `asyncapi/order.yaml`
   - `reserveInventory` from `openapi/warehouse.yaml`
   - `orderAccepted` from `asyncapi/order.yaml`
   - `outForDelivery` from `asyncapi/order.yaml`
   - `getOrderDetails` from `openapi/order.yaml`
5. Connect all the steps in the workflow using white circles on the edges of each step.
6. So far, we have only defined the happy path workflow steps. Now let generate the workflow by clicking on the `Generate Workflow` button in the top right corner of the canvas.
7. This will generate the workflow with all the possible paths.
8. Now let's export the generated workflow as an Arazzo spec by clicking on the `Export Arazzo Spec` button. This will save the generated Arazzo specification as `PlaceOrder.arazzo.yaml`.
9. Specmatic Studio will automatically open the generated Arazzo spec. Review the generated Arazzo spec.
10. Now click on the `Input` tab to provide the input data for the workflow test.
11. Set the first `userEmail` as `blr@specmatic.io` and the second `userEmail` as `del@specmatic.io`. Click on `Save` to save the input data.
12. Now click on the `Test` tab and then click on the `Run` button to run the workflow test. This will execute the entire workflow with the provided input data and validate the interactions between the services based on the defined Arazzo specification.
13. You should see 11 successful assertion in the workflow test results, indicating that the workflow executed successfully.
14. You can click on the `Flow Chart` button to visualize the workflow execution and see the interactions between the services.

Clean up when done:
```shell
docker compose down -v
```
