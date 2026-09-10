# Stateful Mocking: Preserve a CRUD Resource Lifecycle

## Objective
Understand how Specmatic Stateful Mocking makes it easy to build and test state-dependent consumer workflows without relying on a real provider or changing consumer API calls.

## Why this lab matters
A regular mock is stateless in nature. It handles requests independently (without past history) and responds with fresh contract-valid responses. That is useful when you want to test each API operation in isolation, but insufficient when a workflow depends on earlier state. Stateful Mocking maintains an in-memory resource lifecycle across requests.

## Time required to complete this lab
10-15 minutes.

## Prerequisites
- Docker is installed and running.
- A valid Specmatic Enterprise license exists at `labs/license.txt`.
- You are in `labs/stateful-mocking`.
- Ports `8081` and `9100` are available.

## Files in this lab
- `specs/product-api.yaml` - OpenAPI contract for the Product CRUD API.
- `specmatic.yaml` - Controls whether the mock runs in regular or stateful mode.
- `ui/index.html` - Consumer UI and API traffic viewer.
- `docker-compose.yaml` - Consumer and one config-driven mock service.
- `verify-stateless.sh` - Verifies that the regular mock does not preserve the created Product.
- `verify-stateful.sh` - Verifies the complete stateful CRUD lifecycle.

## Learner task
1. Create and fetch a Product with a regular mock; observe that POST state is not preserved.
2. Stop the mock, enable Stateful Mocking in `specmatic.yaml`, and restart it.
3. Create, fetch, update and delete the same Product with Stateful Mocking.

## Lab Rules
- Keep the consumer running while switching mocks.
- Create a fresh product after starting Stateful Mocking.
- Change only the mock type while switching modes.

## Specmatic reference
- [Stateful Mocking](https://docs.specmatic.io/contract_driven_development/service_virtualization/stateful_mocking)

## Part A: Regular mock (intentional failure)
Start the consumer and regular (stateless) mock:

```shell
docker compose up -d --wait consumer mock
```

Open [http://127.0.0.1:8081](http://127.0.0.1:8081).

### 1. Create a Product
1. Keep the default values and click **Create Product**.
2. Expand the POST entry in **API Traffic**.
3. Confirm the response is `HTTP 201` and contains a UUID `id`, name `Wireless Keyboard`, and price `2499`.

### 2. Fetch the same Product
1. Open **Fetch Product**. **Product ID** already contains the ID returned by Create.
2. Without changing the ID, click **Fetch Product**.
3. Expand the GET entry in **API Traffic** and compare it with POST.
4. Confirm GET returns a different contract-valid Product. **It does not return the Product just created.**

Why this happens:
- The same ID did not retrieve the created Product.
- A regular mock handles each request independently and does not remember the POST.

Alternatively, verify this from the command line:

```shell
./verify-stateless.sh
```

```terminaloutput
Stateless behavior verified
```

## Part B: Enable Stateful Mocking
Stop the mock while leaving the consumer running:

```shell
docker compose stop mock
```

Open `specmatic.yaml` and change:

```yaml
type: mock
```

to:

```yaml
type: stateful-mock
```

Alternatively, make this change from the command line:

```shell
sed 's/type: mock/type: stateful-mock/' specmatic.yaml
```

Restart the same mock container:

```shell
docker compose up -d --wait mock
```

Return to the same UI. Create returns a new `id`; the UI fills it into Fetch, Update, and Delete automatically.

### 1. Create a fresh Product
1. Open **Create Product** and click **Create Product**.
2. Expand the new POST entry in **API Traffic**.
3. Confirm POST returns `HTTP 201` with a new Product and ID.

### 2. Fetch it
1. Open **Fetch Product** and click **Fetch Product** without changing the ID.
2. Expand the GET entry and compare it with POST.
3. Confirm GET returns `HTTP 200` with the same ID, name, and price.

### 3. Update it
1. Open **Update Product**. Keep the auto-filled ID and price `2199`.
2. Click **Update Product** and expand the PATCH entry.
3. Confirm PATCH returns `HTTP 200`. Price is `2199`; name remains `Wireless Keyboard`.

### 4. Fetch the update
1. Open **Fetch Product** and click **Fetch Product** again.
2. Expand the newest GET entry.
3. Confirm GET returns `HTTP 200` with price `2199` and the original name.

### 5. Delete it
1. Open **Delete Product** and click **Delete Product** without changing the ID.
2. Expand the DELETE entry.
3. Confirm DELETE returns `HTTP 204` with no response body.

### 6. Fetch after deletion
1. Open **Fetch Product** and click **Fetch Product** once more.
2. Expand the newest GET entry.
3. Confirm GET returns `HTTP 404`. The Product no longer exists.

Why this works:
- Stateful Mocking preserved the Product through create, fetch, update, and delete.

Alternatively, verify the complete lifecycle from the command line:

```shell
./verify-stateful.sh
```

```terminaloutput
Stateful CRUD lifecycle verified
```

## Pass criteria
- Regular mock: POST returns an ID, but GET does not preserve that created Product.
- Stateful Mocking: the complete create/update/delete lifecycle behaves as shown above.
- Consumer URL and API calls remain unchanged across the switch.

## Common confusion points
- If port `9100` is already allocated, stop the process using it before starting this lab.
- Stateful Mocking keeps runtime state in memory. Restarting the Stateful Mock clears resources created during the session.
- Create a fresh product after switching; IDs from the stopped regular mock were never stored.

## Cleanup

```shell
docker compose down -v --remove-orphans
```

## What you learned
- Regular mocks handle calls independently and can generate fresh contract-valid responses.
- Stateful Mocking preserves a CRUD resource lifecycle in memory.
- Stateful behavior can be enabled without changing the consumer or its API calls.

## Next step
If you are doing this lab as part of an eLearning course, return to the eLearning site and continue with the next module.
