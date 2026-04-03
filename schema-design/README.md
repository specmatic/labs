# Lab: Schema Design for Mutually Exclusive Request Shapes

## Objective
Model mutually exclusive request shapes correctly so Specmatic schema resiliency tests generate meaningful requests.

## Time required to complete this lab
10-15 minutes.

## Prerequisites
- Docker is installed and running.
- You are in `labs/schema-design`.
- Port `8080` is available.

## Files in this lab
- `specs/payment-api.yaml`: OpenAPI contract with an intentional modeling mistake.
- `service/server.py`: Provider implementation that enforces real business validation.
- `specmatic.yaml`: Specmatic config with `schemaResiliencyTests: positiveOnly`.
- `docker-compose.yaml`: Starts provider and contract test runner.

## Learner task
Refactor the request schema in `specs/payment-api.yaml` from “all optional groups under one object” to `oneOf` with a discriminator on `paymentType`.

## Why this lab matters
A common antipattern is making both groups optional in one schema:
- Card fields (`cardNumber`, `cardExpiry`, `cardCvv`)
- Bank transfer fields (`bankAccountNumber`, `bankRoutingNumber`, `bankAccountHolder`)

When modeled this way, schema resiliency tests can generate requests like `{ "paymentType": "card" }` with no card details. Contract sees it as valid, but implementation rejects it. This creates test failures which could have been avoided with a oneOf schema along with a discriminator in the specification.

## Lab Rules
- Do not edit `service/server.py`.
- Do not edit `docker-compose.yaml`.
- Edit only `specs/payment-api.yaml`.

## Specmatic references
- Schema resiliency tests: [https://docs.specmatic.io/documentation/contract_tests.html#schema-resiliency-testing](https://docs.specmatic.io/documentation/contract_tests.html#schema-resiliency-testing)
- OpenAPI `oneOf` and discriminator: [https://swagger.io/docs/specification/v3_0/data-models/oneof-anyof-allof-not/](https://swagger.io/docs/specification/v3_0/data-models/oneof-anyof-allof-not/)

## 1. Baseline run (intentional failure)
Run:

```shell
docker compose up contract-test --build --abort-on-container-exit
```

Expected output:
```terminaloutput
Tests run: 4, Successes: 2, Failures: 2, Errors: 0
```

Failure reason points to `POST /payments` where requests like `{ "paymentType": "card" }` and `{ "paymentType": "bank_transfer" }` are contract-valid but service returns `400` instead of expected `201`.

Clean up:

```shell
docker compose down -v
```

## 2. Fix the contract model
Open `specs/payment-api.yaml` and update `PaymentRequest` to this shape:

1. Create `CardPaymentRequest` with following `required` fields:
   - `paymentType` (enum: `card`)
   - `cardNumber` (type: `string`)
   - `cardExpiry` (type: `string`)
   - `cardCvv` (type: `string`)
2. Create `BankTransferPaymentRequest` with following `required` fields:
   - `paymentType` (enum: `bank_transfer`)
   - `bankAccountNumber` (type: `string`)
   - `bankRoutingNumber` (type: `string`)
   - `bankAccountHolder` (type: `string`)
3. Replace `PaymentRequest` with:
   - `oneOf` referencing those two schemas
   - `discriminator.propertyName: paymentType`
   - mapping for `card` to `CardPaymentRequest` and `bank_transfer` to `BankTransferPaymentRequest`

```yaml
    CardPaymentRequest:
      type: object
      required:
        - paymentType
        - cardNumber
        - cardExpiry
        - cardCvv
      properties:
        paymentType:
          type: string
          enum: [ card ]
        cardNumber:
          type: string
        cardExpiry:
          type: string
        cardCvv:
          type: string
    BankTransferPaymentRequest:
      type: object
      required:
        - paymentType
        - bankAccountNumber
        - bankRoutingNumber
        - bankAccountHolder
      properties:
        paymentType:
          type: string
          enum: [ bank_transfer ]
        bankAccountNumber:
          type: string
        bankRoutingNumber:
          type: string
        bankAccountHolder:
          type: string
    PaymentRequest:
      oneOf:
        - $ref: "#/components/schemas/CardPaymentRequest"
        - $ref: "#/components/schemas/BankTransferPaymentRequest"
      discriminator:
        propertyName: paymentType
        mapping:
          card: "#/components/schemas/CardPaymentRequest"
          bank_transfer: "#/components/schemas/BankTransferPaymentRequest"
```

## 3. Re-run contract tests
Run:

```shell
docker compose up contract-test --build --abort-on-container-exit
```

Expected output:
```terminaloutput
Tests run: 2, Successes: 2, Failures: 0, Errors: 0
```

Clean up:

```shell
docker compose down -v
```

## Pass criteria
- Baseline run fails on invalidly modeled optional-group scenario.
- After schema refactor to `oneOf` + discriminator, all tests pass.

## Next step
If you are doing this lab as part of an eLearning course, return to the eLearning site and continue with the next module.
