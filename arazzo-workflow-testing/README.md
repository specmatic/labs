# API Workflow Testing using Arazzo

Want to test the functionality of an entire business workflow of your microservices architecture that involves both synchronous HTTP calls and asynchronous event-driven interactions?

![Order Application Workflow](assets/arazzo-workflow.gif)

## Time required to complete this lab:
10-15 minutes.

## Prerequisites
- Docker is installed and running.
- You are in `labs/arazzo-workflow-testing`.

## API Workflow Testing Overview Video
[![Watch the video](https://img.youtube.com/vi/baYcsznD_Mk/hqdefault.jpg)](https://www.youtube.com/watch?v=baYcsznD_Mk)

## Sequence Diagram

![Sequence Diagram](./assets/flow.svg)

Using a simple drag-and-drop approach, Specmatic-Arazzo facilitates generating an entire workflow and exporting it as an industry-standard Arazzo specification. Once you've created the Arazzo specification, you can leverage Specmatic-Arazzo to perform end-to-end workflow testing and mocking for your microservices architecture.

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
