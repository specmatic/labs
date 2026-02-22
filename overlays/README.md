# Studio Lab: Fix Path Mismatch Using Overlays

This lab demonstrates a common real-world issue:

- The consumer expects `GET /api/users/{id}`
- The deployed provider exposes `GET /api/v1/users/{id}`

**Note**: if this `/v1 prefix` was right at the beginning of the path, it would be easier to fix by just changing the `basePath` in `specmatic.yaml`. But in this case, the version prefix is in the middle of the path, which makes it more difficult to fix without modifying the original spec.

Because of this path mismatch, contract tests fail. Your goal is to use a Specmatic overlay to patch the consumer contract at test time, without modifying the original spec.

## Files in this lab
- `specs/my-service.yaml` - Service contract (older path: `/api/users/{id}`)
- `provider/server.py` - Tiny real HTTP service that only exposes `/api/v1/users/{id}`
- `provider/Dockerfile` - Container image for the provider service
- `overlays/path-prefix.overlay.yaml` - Overlay file you will update
- `specmatic.yaml` - Specmatic config where you will enable `overlayFilePath`
- `docker-compose.yaml` - Runs the real provider service and contract tests against it

## Run baseline tests (expected to fail)
From this folder, run:

```shell
docker compose up
```

Expected outcome:
- The test run fails because requests are generated for `/api/users/{id}` while the provider serves `/api/v1/users/{id}`.
- If you inspect the failing HTTP exchange, the provider responds with `404 Not Found` for `/api/users/{id}`.

Stop and clean up:

```shell
docker compose down
```

## Goal of this lab
Make the tests pass by applying an overlay that rewrites the path from `/api/users/{id}` to `/api/v1/users/{id}`.

Important constraint:
- Do not edit `specs/my-service.yaml`

## Step 1: Update the overlay file
Open `overlays/path-prefix.overlay.yaml` and replace `actions: []` with the following actions:

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

Note:
- Reusing `components.parameters` and `components.responses` helps avoid repeating the same parameter and response payload details.

## Step 2: Enable overlay in Specmatic config
Open `specmatic.yaml` and uncomment:

```yaml
overlayFilePath: ./overlays/path-prefix.overlay.yaml
```

It should be under `systemUnderTest.service.runOptions.openapi.specs[].spec`.

## Re-run tests (expected to pass)

```shell
docker compose up
```

Expected outcome:
- Contract tests pass, because Specmatic applies the overlay before running tests.

You should see one successful test and no failures.

Stop and clean up:

```shell
docker compose down
```

## What you learned
- Overlays let you adapt contracts for environment-specific differences.
- You can patch paths (and other parts of specs) without changing the source contract file.
- `overlayFilePath` in `specmatic.yaml` is a practical way to apply overlays in a repeatable test setup.

Learn more: [Specmatic Overlays Documentation](https://docs.specmatic.io/features/overlays)
