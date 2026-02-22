# API Workflow Testing using Arazzo

Want to test the functionality of an entire business workflow of your microservices architecture that involves both synchronous HTTP calls and asynchronous event-driven interactions?

![Order Appplication Workflow](assets/arazzo-workflow.gif)

## Time required to complete this lab:
10-15 minutes.

## Sequency Diagram

![Sequency Diagram](./assets/flow.svg)

Using a simple drag-and-drop approach, Specmatic-Arazzo facilitates the generation of an entire workflows and exporting that as an industry-standard Arazzo Specification. Once you've created the Arazzo specification, you can leverage Specmatic-Arazzo to perform end-to-end workflow testing and mocking of your microservices architecture.

More details: https://docs.specmatic.io/supported_protocols/arazzo

## Getting Started

Start the full stack using Docker Compose:

```shell
docker compose up --build
```

Start Studio
```shell
docker run --rm --network host -v ./specs:/usr/src/app specmatic/enterprise studio
```

This launches the following services:

| Service           | Port | Description                    |
| ----------------- | ---- | ------------------------------ |
| **Location API**  | 3000 | Provides user location details |
| **Products API**  | 3001 | Returns products by location   |
| **Order API**     | 3002 | Handles order lifecycle        |
| **Warehouse API** | 3003 | Manages inventory operations   |
| **Kafka**         | 9092 | Internal broker port           |
| **Postgres**      | 5432 | Shared database                |

Clean up when done:
```shell
docker compose down -v
```
