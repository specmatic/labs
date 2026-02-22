# Studio Lab: Dictionary to Generate Domain-Aware Request/Response Payloads

## Objective
Understand how you can use Specmatic Dictionary feature to generate deterministic, domain-aware request payloads from contract testing and response from service virtualization.

## Time required to complete this lab:
10-15 minutes.

## Prerequisites
- Docker is installed and running.
- You are in `labs/dictionary`.

## Files in this lab
- `specs/simple-openapi-spec.yaml` - OpenAPI spec for the BFF API (source of truth for this lab).
- `examples/*.json` - External examples used by tests.
- `specmatic.yaml` - Specmatic config file that defines the spec and examples.

## 1. Run loop test using Docker (intentional failure)
```shell
docker compose up test --abort-on-container-exit
```

Expected output:
```terminaloutput
Tests run: 3, Successes: 0, Failures: 3, Errors: 0
```

### Root cause of the failed tests
Tests expect specific response values, but the mock generates random valid values.  
We will fix this by configuring dictionary-driven mock generation, not by editing the example test files.

Clean up before the next step:
```shell
docker compose down
```

## 2. Learner task: configure dictionary-based mock data
Generate dictionary data from existing examples:
```shell
docker run --rm -v .:/usr/src/app specmatic/enterprise examples dictionary --examples-dir examples --spec-file specs/simple-openapi-spec.yaml --out specs/dictionary.yaml
```

Open and understand the [generated dictionary file](specs/dictionary.yaml)

Update `specmatic.yaml` under `dependencies.services[0].service` to add:
```yaml
data:
  dictionary:
    path: specs/dictionary.yaml
```

## 3. Re-run loop test after configuring dictionary
```shell
docker compose up test --abort-on-container-exit
```

Expected output:
```terminaloutput
Tests run: 3, Successes: 3, Failures: 0, Errors: 0
```

Clean up:
```shell
docker compose down
```

## Pass Criteria
- Baseline run fails with `Tests run: 3, Successes: 0, Failures: 3, Errors: 0`.
- After dictionary configuration, run passes with `Tests run: 3, Successes: 3, Failures: 0, Errors: 0`.
