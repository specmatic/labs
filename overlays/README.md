# Studio Lab: Fix Path Mismatch Using Overlays

## Objective
Use a Specmatic overlay to patch a contract path mismatch at test time, without modifying the source contract.

## Time required to complete this lab:
10-15 minutes.

## Prerequisites
- Docker is installed and running.
- You are in `labs/overlays`.

## Files in this lab
- `specs/my-service.yaml` - Service contract (older path: `/api/users/{id}`)
- `provider/server.py` - Tiny real HTTP service that only exposes `/api/v1/users/{id}`
- `provider/Dockerfile` - Container image for the provider service
- `overlays/path-prefix.overlay.yaml` - Overlay file you will update
- `specmatic.yaml` - Specmatic config where you will enable `overlayFilePath`
- `docker-compose.yaml` - Runs the real provider service and contract tests against it

## Learner task
Fix the failing contract test by:
1. adding overlay actions that replace `/api/users/{id}` with `/api/v1/users/{id}`
2. enabling that overlay in `specmatic.yaml`
3. re-running tests to confirm pass state

## Lab Rules
- Do not edit `specs/my-service.yaml`.
- Do not edit `provider/server.py`.
- Make changes only in:
  - `overlays/path-prefix.overlay.yaml`
  - `specmatic.yaml`

## Scenario Context
This lab demonstrates a common real-world issue:

- The consumer expects `GET /api/users/{id}`
- The deployed provider exposes `GET /api/v1/users/{id}`

**Note**: if this `/v1 prefix` was right at the beginning of the path, it would be easier to fix by just changing the `basePath` in `specmatic.yaml`. But in this case, the version prefix is in the middle of the path, which makes it more difficult to fix without modifying the original spec.

Because of this path mismatch, contract tests fail. Your goal is to use a Specmatic overlay to patch the consumer contract at test time, without modifying the original spec.

## References
- Overlays feature: [https://docs.specmatic.io/features/overlays](https://docs.specmatic.io/features/overlays)

## Intentional failure (Baseline run)
Run:

```shell
docker compose up test --abort-on-container-exit
```

Expected output:
- `Tests run: 1, Successes: 0, Failures: 1, Errors: 0`
- The test run fails because requests are generated for `/api/users/{id}` while the provider serves `/api/v1/users/{id}`.
- In the failing HTTP exchange, provider responds with `404 Not Found` for `/api/users/{id}`.

Clean up:

```shell
docker compose down -v
```

## Step 1: Update the overlay file
Open `overlays/path-prefix.overlay.yaml`.

Replace this:
```yaml
actions: []
```

With:

```yaml
actions:
  - target: "$.paths"
    update:
      /api/v1/users/{id}:
        get:
          summary: Get user by id
          parameters:
            - $ref: "#/components/parameters/UserIdPathParam"
          responses:
            "200":
              $ref: "#/components/responses/User200"

  - target: "$.paths['/api/users/{id}']"
    remove: true
```

Important:
- Keep exactly one top-level `actions` key in this file.
- Reusing `components.parameters` and `components.responses` helps avoid repeating the same parameter and response payload details.

## Step 2: Enable overlay in Specmatic config
Open `specmatic.yaml`, go to:

`systemUnderTest.service.runOptions.openapi.specs[0].spec`

Uncomment this line:

```yaml
overlayFilePath: ./overlays/path-prefix.overlay.yaml
```

## Pass verification
Run:
```shell
docker compose up test --abort-on-container-exit
```

Expected output:
- `Tests run: 1, Successes: 1, Failures: 0, Errors: 0`
- Contract tests pass, because Specmatic applies the overlay before running tests.

Clean up:

```shell
docker compose down -v
```

## Pass Criteria
- Baseline run fails with 404 path mismatch (`/api/users/{id}`).
- After overlay + config update, test run passes fully.

## What you learned
- Overlays let you adapt contracts for environment-specific differences.
- You can patch paths (and other parts of specs) without changing the source contract file.
- `overlayFilePath` in `specmatic.yaml` is a practical way to apply overlays in a repeatable test setup.
