# Lab: OpenAPI Linting and Governance

## Objective
Learn how to use **Specmatic Linter** to enforce API quality and design consistency, explore active rules using the `get-rules` catalog, inspect interactive HTML lint reports, fix contract violations, and customize governance policies using rulesets, profiles, `include`, `override`, and `exclude`.

## Time required to complete this lab
10-15 minutes.

## Prerequisites
- Docker Engine is installed and running on your machine.
- You are in the `labs/openapi-linter` directory.
- A valid Specmatic Enterprise license exists at `labs/license.txt`.

## Why this lab matters

Specmatic Linter provides automated, shift-left governance for API contracts:

1. **Semantic validation**: Catches logical and protocol issues that standard YAML/JSON parsers miss (e.g. declaring a header parameter that contradicts the body's media type, or invalid enum types).
2. **Progressive adoption ladder**: Allows teams to adopt standards incrementally through built-in rulesets (`starter` -> `lenient` -> `recommended` -> `strict` -> `complete`) rather than failing every build on day one.
3. **Flexible policy tuning**: Teams can adapt global rulesets to specific environments using profiles, pull in rules via `include`, customize rule severities via `override`, and skip non-applicable rules via `exclude`.

## Specmatic Documentation References
- [OpenAPI Linting Overview](https://docs.specmatic.io/category/openapi)
- [Built-in Rules & Rulesets](https://docs.specmatic.io/features/linter/specification-formats/openapi/built-in-rules)
- [Profiles & Default Profile](https://docs.specmatic.io/features/linter/specification-formats/openapi/profiles)
- [Configuration Reference](https://docs.specmatic.io/features/linter/specification-formats/openapi/configuration)

## Files in this lab
- `openapi.yaml`: OpenAPI 3.0 specification with intentional errors and warnings.
- `specmatic-linter.yaml`: Linter configuration with the `starter` ruleset, additional rules, and a severity override.

---

## Step 1: Run the Linter and Observe the Failure

Run the linter on the provided `openapi.yaml` spec file.

```shell
docker run --rm \
  -v ".:/usr/src/app" \
  -v "${PWD}/../license.txt:/specmatic/specmatic-license.txt:ro" \
  -e SPECMATIC_LICENSE_PATH=/specmatic/specmatic-license.txt \
  specmatic/enterprise:latest \
  lint openapi.yaml --config specmatic-linter.yaml --format=html
```

Since we've specified `--format=html`, this command will generate an interactive HTML report to review the lint results.

Expected terminal output:
```terminaloutput
Lint report for openapi.yaml generated at /usr/src/app/build/reports/specmatic/lint/openapi/lint-report-openapi.html
Target: openapi.yaml
Maturity Level: Gold
Errors: 1, Warnings: 3, Ignored: 0
Status: FAILED
```

> [!NOTE]
> The command exits with code `1` (`Status: FAILED`) because there is **1 error**.

### Inspect the Diagnostics HTML Report
Open [build/reports/specmatic/lint/openapi/lint-report-openapi.html](build/reports/specmatic/lint/openapi/lint-report-openapi.html) in your browser.

Confirm that the report shows **1 error** and **3 warnings**. In the next step, trace these diagnostics back to the specification.

---

## Step 2: Understand the Error and Warnings

Keep the lint report open and inspect `openapi.yaml`. The reported error and warnings correspond to these issues in the Users API:

1. **Content-Type Header Conflict (`content-type-header-overrides-media-type`, Error)**:
   Under `POST /users`, the request body declares `application/json`, but an explicit header parameter named `Content-Type` is defined with `application/xml`:
   ```yaml
   paths:
     /users:
       post:
         summary: Create user
         # ❌ Conflict: Content-Type header contradicts requestBody media type
         parameters:
           - name: Content-Type
             in: header
             required: true
             schema:
               type: string
               enum:
                 - application/xml
         requestBody:
           content:
             application/json:
               schema: ...
   ```
   In OpenAPI 3.x, request media types should be defined in `requestBody.content`. Declaring an explicit `Content-Type` header parameter that contradicts `requestBody.content` creates ambiguity for clients and servers.

2. **Enum Type Contradiction (`no-enum-type-mismatch`, Warning)**:
   In schema `userType`, the type is declared as `integer`, but one of the enum values is a string (`"inactive"`):
   ```yaml
       # ⚠️ Type contradiction: enum value "inactive" contradicts integer schema
       userType:
         type: integer
         minimum: 1
         maximum: 10
         enum: [1, 2, "inactive"]
   ```

3. **Sibling Properties next to `$ref` (`ref-has-siblings`, Warning)**:
   In schema `userStatus`, `$ref` is placed alongside sibling properties (`description`). In OAS 3.0, any sibling properties alongside `$ref` are ignored by OpenAPI parsers:
   ```yaml
       # ⚠️ Warning: $ref must not have sibling properties in OAS 3.0
       userStatus:
         $ref: '#/components/schemas/statusType'
         description: Status of user account
   ```

The third warning, `health-endpoint`, flags the missing `/health` monitoring endpoint. This is an organizational standard enforced by the lint configuration.

The error makes the lint command fail. Next, inspect the configuration to understand why these rules were applied and why the Content-Type conflict has severity `error`.

---

## Step 3: Understand `specmatic-linter.yaml` with `include` and `override`

The lint command you ran loaded `specmatic-linter.yaml` through `--config`. Review this file to understand the policy behind the diagnostics.

### Understanding Rulesets, Profiles, and Customizations
- **Ruleset**: A curated bundle of rules with predefined severities (`starter`, `lenient`, `recommended`, `strict`, `complete`). The `starter` ruleset includes core syntax and structural rules.
- **Profile**: A named configuration targeting a specific context (e.g., `default`, `public-api`, `internal`). When you run the linter without passing `--profile <name>`, Specmatic automatically loads the profile named `default`.
- **`include`**: Pulls additional rules into the active profile. This allows teams to adopt specific organizational standards without enabling an entire large ruleset all at once.
- **`override`**: Customizes the severity of a rule (e.g. elevating a rule from `warn` to `error`, or relaxing an `error` to `warn`).

In this lab, we start with the `starter` ruleset and selectively pull in:
- `content-type-header-overrides-media-type` (elevated from warning to a blocking `error` using `override`)
- `ref-has-siblings` (advisory warning)
- `health-endpoint` (organizational health check standard)

Open `specmatic-linter.yaml` in your editor and review the configuration.

---

## Step 4: Run `get-rules` to Inspect the Rules Catalog

Now run `get-rules` with the same configuration to see the active rules and severities used in the initial lint run.

```shell
docker run --rm \
  -v ".:/usr/src/app" \
  -v "${PWD}/../license.txt:/specmatic/specmatic-license.txt:ro" \
  -e SPECMATIC_LICENSE_PATH=/specmatic/specmatic-license.txt \
  specmatic/enterprise:latest \
  lint get-rules --config specmatic-linter.yaml
```

Expected terminal output:
```terminaloutput
Generated rules catalog at /usr/src/app/build/reports/specmatic/lint/openapi/rules-report.html
```

### Inspect the Rules Catalog HTML Report
Open the generated report in your web browser:
[build/reports/specmatic/lint/openapi/rules-report.html](build/reports/specmatic/lint/openapi/rules-report.html)

Filter by version using the `+` key and selecting `oas3_0` and filter the severity using the `+` key and selecting `error` or `warn` or both.

Notice that in the table, `content-type-header-overrides-media-type` is listed with severity **`error`** due to our `override` configuration!
You can search for this rule using the `Quick search` feature.

This catalog shows the active rules with their severity.

---

## Step 5: Fix the Specification and Exclude Warnings

We will resolve this failure by:
1. **Fixing contract defects** directly in `openapi.yaml`.
2. **Excluding organizational warnings** in `specmatic-linter.yaml` that do not apply to this service.

### 5A. Fix `openapi.yaml`
Open `openapi.yaml` and make the following edits:

**1. Remove the explicit `Content-Type` header parameter (fixes `content-type-header-overrides-media-type`):**
In OAS 3.x, request payload types belong under `requestBody.content`. Remove the `parameters:` section under `post:` so it looks like:
```yaml
  /users:
    post:
      tags:
        - users
      summary: Create user
      description: Creates a new user
      operationId: createUser
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              properties:
                name:
                  type: string
                  maxLength: 50
      responses:
        '201':
          description: User created
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/userResponse'
```

**2. Remove sibling property from `$ref` (fixes `ref-has-siblings`):**
Under `components.schemas.userStatus`, remove `description: Status of user account` and add it to `statusType` instead:
```yaml
    userStatus:
      $ref: '#/components/schemas/statusType'

    statusType:
      type: string
      maxLength: 20
      description: Status of user account
```

**3. Fix enum types (fixes `no-enum-type-mismatch`):**
Under `components.schemas.userType`, remove `"inactive"` from the enum values so all entries match the integer type:
```yaml
    userType:
      type: integer
      format: int32
      minimum: 1
      maximum: 10
      enum: [1, 2, 3]
      description: User account type code
```

Alternatively, apply the complete corrected specification from the command line:

```shell
docker run --rm -v ".:/usr/src/app" --entrypoint sh specmatic/enterprise:latest -c 'cp .backup/openapi-fixed.yaml openapi.yaml'
```

### 5B. Tune Policy Using `exclude:`
Some API standards in a ruleset might not be relevant for every microservice. For instance, our service may be deployed behind an API gateway or service mesh where health checks and liveness probes are handled by infrastructure rather than the microservice contract itself.

We can turn off specific rules using the `exclude:` key under `rules:` in `specmatic-linter.yaml`.

Update `specmatic-linter.yaml`:

```yaml
profiles:
  default:
    rules:
      extends:
        - starter
      include:
        - content-type-header-overrides-media-type
        - ref-has-siblings
        - health-endpoint
      override:
        content-type-header-overrides-media-type: error
      exclude:
        - health-endpoint
```

Alternatively, apply this configuration from the command line:

```shell
docker run --rm -v ".:/usr/src/app" --entrypoint sh specmatic/enterprise:latest -c 'cp .backup/specmatic-linter-exclude.yaml specmatic-linter.yaml'
```

---

## Step 6: Re-run the Linter and Confirm Passing Result

Now re-run the linter to verify that the errors have been resolved and the excluded rule is ignored:

```shell
docker run --rm \
  -v ".:/usr/src/app" \
  -v "${PWD}/../license.txt:/specmatic/specmatic-license.txt:ro" \
  -e SPECMATIC_LICENSE_PATH=/specmatic/specmatic-license.txt \
  specmatic/enterprise:latest \
  lint openapi.yaml --config specmatic-linter.yaml --format=html
```

Expected terminal output:
```terminaloutput
Lint report for openapi.yaml generated at /usr/src/app/build/reports/specmatic/lint/openapi/lint-report-openapi.html
Target: openapi.yaml
Maturity Level: Platinum
Errors: 0, Warnings: 0, Ignored: 1
Status: PASSED
```

### Review the Results
Refresh [build/reports/specmatic/lint/openapi/lint-report-openapi.html](build/reports/specmatic/lint/openapi/lint-report-openapi.html) in your browser:
- **`Errors: 0`**: All semantic blockers have been resolved.
- **`Warnings: 0`**: All contract warnings have been fixed.
- **`Ignored: 1`**: The excluded rule (`health-endpoint`) is tracked as ignored.
- **`Status: PASSED`**: The check succeeds with exit code `0`.
- **`Maturity Level: Platinum`**: The API now satisfies all active maturity rules in this profile.

---

## Cleanup
To remove the generated report directory:

```shell
docker run --rm \
  -v ".:/usr/src/app" \
  --entrypoint sh \
  specmatic/enterprise:latest -c 'rm -rf build'
```

---

## Pass Criteria
1. Initial lint run fails with `Errors: 1, Warnings: 3, Ignored: 0` and `Status: FAILED`.
2. `get-rules` generates `build/reports/specmatic/lint/openapi/rules-report.html`.
3. After fixing contract defects and adding `exclude: [health-endpoint]` in `specmatic-linter.yaml`, the linter run passes with `Errors: 0, Warnings: 0, Ignored: 1`, and `Status: PASSED`.

## Next Step
If you are doing this lab as part of a workshop or course, return to the workshop materials to proceed to the next module.
