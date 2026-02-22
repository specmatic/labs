# Quick Start Mock: Unblock Consumer Development

This lab demonstrates how to keep a consumer moving when a dependent service is not ready or available.

## Goal
Run a simple consumer app that calls `GET /pets/1`.
- First, see it fail when the service is unavailable.
- Then start a Specmatic mock server from contract and see the consumer work immediately.

## Time required to complete this lab:
10-15 minutes.

## Prerequisites
- Docker Engine running
- Ports `8081`, `9000`, and `9100` available

## Files in this lab
- `specs/service.yaml` - OpenAPI contract for the pet API
- `ui/index.html` - Tiny consumer app (browser-based) that fetches `/pets/{petid}`
- `docker-compose.yaml` - Consumer service and optional mock service

## Part A: Start only the consumer (service unavailable)
```shell
docker compose up consumer --build
```

Open [http://127.0.0.1:8081](http://127.0.0.1:8081).

In the consumer app, keep base URL as `http://127.0.0.1:9100`, keep Pet ID as `1`, and click **Load Pet**.

Expected result:
- You see `Service unavailable`.

This simulates the backend not being ready.

## Part B: Start Specmatic mock server
In a second terminal, run:

```shell
docker compose --profile mock up mock
```

Go back to the consumer app and click **Load Pet** again.

Expected result:
- Status shows `Success`
- The consumer displays mocked pet data from the contract.

Try changing **Pet ID** to different values (for example `2`, `101`, `abc`) and click **Load Pet** to see how the mock responds to valid and invalid path values.

**Key point**: The mock server behavior is generated from the contract (OpenAPI Specification). Zero lines of code required to create a working mock that meets consumer expectations.

## Part C: Stop mock and observe fallback

```shell
docker compose --profile mock down
```

Click **Load Pet** again in the consumer app.

Expected result:
- It goes back to `Service unavailable`.

## Part D: Run the mock from Studio and inspect traffic
Start Studio in a new terminal:

```shell
docker run --rm --network host \
  -v .:/usr/src/app \
  -v ../license.txt:/specmatic/specmatic-license.txt:ro \
  specmatic/enterprise:latest \
  studio
```

Open [Studio](http://localhost:9000/_specmatic/studio).

In Studio:
1. From the left sidebar, open `specs/service.yaml` from the left panel.
2. Go to the **Mock** tab.
3. Set mock port to `9100`.
4. Click **Run** to start the mock.

Now go back to the consumer app at [http://127.0.0.1:8081](http://127.0.0.1:8081) and click **Load Pet**.

To inspect request/response in Studio:
1. Return to the **Mock** tab for `service.yaml`.
2. Click on the Result cell of `GET /pets/{petid}`.
3. Click on the `Scenario: GET /pets/(petid:number) -> 200` to review full request headers/body and response status/body.

In the UI, try different Pet IDs and inspect the corresponding traffic in Studio.

This gives you a clean visual trace of what the consumer sent and what the contract-driven mock returned.

## Cleanup
Stop Studio by pressing `Cltr+c` and the mock server:
```shell
docker compose down
```

## What you learned
- Mocking lets consumer teams continue independently of dependency readiness.
- Specmatic mock behavior is generated from the contract (Industry standard specifications), so consumer expectations and contract stay aligned.
- The generated mock is intelligent and resilient to contract changes, so it continues to work as the contract evolves.
- The generated mock is wire-compatible with the real service, so consumer tests against the mock are valid against the real service.
- You can quickly switch between unavailable dependency and contract-driven mock without changing consumer code.
