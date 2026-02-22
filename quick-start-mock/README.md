# Quick Start Mock: Unblock Consumer Development

## Objective
Use a contract-generated Specmatic mock to keep a consumer app moving even when the real provider is unavailable.

## Why this lab matters
In real projects, consumer teams are often blocked because a dependency is late, unstable, or not accessible in local environments. This lab shows how to remove that dependency bottleneck by generating a mock directly from the contract.

## Time required to complete this lab:
10-15 minutes.

## Prerequisites
- Docker is installed and running.
- You are in `labs/quick-start-mock`.
- Ports `8081`, `9000`, `9001`, and `9100` are available.

## Files in this lab
- `specs/service.yaml` - OpenAPI contract for the pet API.
- `ui/index.html` - Consumer UI that calls `GET /pets/{petid}`.
- `docker-compose.yaml` - Consumer service and optional mock service profile.

## Learner task
1. Start consumer without provider and observe failure.
2. Start Specmatic mock from contract and observe consumer success.
3. Stop only the mock and observe consumer fallback.
4. Run mock from Studio and inspect traffic.

## Lab Rules
- Do not edit `specs/service.yaml`.
- Do not edit consumer UI code.
- Use only commands in this README.

## Specmatic references
- Service virtualization and mocks: [https://docs.specmatic.io/documentation/service_virtualization.html](https://docs.specmatic.io/documentation/service_virtualization.html)
- Running Specmatic mock from contract: [https://docs.specmatic.io/documentation/command_line.html#mock](https://docs.specmatic.io/documentation/command_line.html#mock)
- Specmatic Studio: [https://docs.specmatic.io/documentation/studio.html](https://docs.specmatic.io/documentation/studio.html)

## Part A: Baseline run (intentional failure)
Start only the consumer:

```shell
docker compose up consumer --build
```

Open [http://127.0.0.1:8081](http://127.0.0.1:8081).

In the UI:
- Base URL: `http://127.0.0.1:9100`
- Pet ID: `1`
- Click **Load Pet**

Expected output:
- Status shows `Service unavailable`.

Why this fails:
- Consumer is running.
- Provider at `:9100` is not running yet.

## Part B: Start contract-generated mock (consumer unblocked)
Keep Part A terminal running. In a second terminal, run:

```shell
docker compose --profile mock up mock
```

Go back to consumer UI and click **Load Pet** again.

Expected output:
- Status shows `Success`
- JSON response is returned for pet id `1`.

Try additional IDs:
- `2` -> success with contract-generated data
- `abc` -> error response (`400`) because path parameter must be numeric

## Part C: Stop only the mock and observe fallback
In the terminal where mock is running, press `Ctrl+C`.

Clean up:
```shell
docker compose --profile mock stop mock
```

Go back to consumer UI and click **Load Pet** again.

Expected output:
- Status returns to `Service unavailable`.

## Part D: Run mock from Studio and inspect traffic
Start Studio in a new terminal:

```shell
docker run --rm \
  -v .:/usr/src/app \
  -v ../license.txt:/specmatic/specmatic-license.txt:ro \
  -p 9000:9000 \
  -p 9001:9001 \
  specmatic/enterprise:latest \
  studio
```

Open [http://127.0.0.1:9000/_specmatic/studio](http://127.0.0.1:9000/_specmatic/studio).

In Studio:
1. From the left sidebar, open `specs/service.yaml`.
2. Go to the **Mock** tab.
3. Set mock port to `9100`.
4. Click **Run**.

Now use consumer UI again and click **Load Pet**.

To inspect mock traffic in Studio:
1. In **Mock** tab, open `GET /pets/{petid}` result.
2. Open `Scenario: GET /pets/(petid:number) -> 200`.
3. Review request and response details.

## Pass criteria
- Without mock: consumer shows `Service unavailable`.
- With mock running: consumer shows `Success` and returns JSON.
- After stopping mock: consumer returns to `Service unavailable`.

## Common confusion points
- Using `down` during Part C can stop consumer too; use `Ctrl+C` or `stop mock` to stop only mock.
- Trying to open Studio on `localhost` in environments where IPv6 causes issues; use `127.0.0.1`.
- Assuming this lab needs `specmatic.yaml`; this quick-start runs mock directly from `specs/service.yaml`.

## Cleanup
From lab folder:

```shell
docker compose --profile mock down -v
```

If consumer is still running in another terminal, stop it with `Ctrl+C`.

## What you learned
- Mocking lets consumer teams continue independently of dependency readiness.
- Specmatic mock behavior is generated from the contract (Industry standard specifications), so consumer expectations and contract stay aligned.
- The generated mock is intelligent and resilient to contract changes, so it continues to work as the contract evolves.
- The generated mock is wire-compatible with the real service, so consumer tests against the mock are valid against the real service.
- You can quickly switch between unavailable dependency and contract-driven mock without changing consumer code.
