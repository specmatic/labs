# Backward Compatibility Testing

## Objective
Use Specmatic's `backward-compatibility-check` command to catch a breaking API contract change before it is committed.

## Why this lab matters
Backward compatibility checks shift API governance left:
1. The git-tracked contract on `origin/main` is your baseline.
2. Your uncommitted change is the proposed API evolution.
3. Specmatic compares the two and flags breaking changes immediately.

This helps teams detect consumer-impacting contract changes during design and code review, instead of during regression testing or after release.

## Time required to complete this lab:
10-15 minutes.

## Prerequisites
- Docker is installed and running.
- Git is installed.
- You are in `labs/backward-compatibility-testing`.

## Files in this lab
- `products.yaml` - The baseline OpenAPI contract already tracked in git.

## Architecture
- The tracked contract on `origin/main` is the old contract version.
- Your local edit to `products.yaml` is the proposed new contract version.
- Specmatic compares the edited file to the git-tracked baseline and reports compatibility.

## Learner task
Keep the newly added `category` field, but make the contract backward compatible again by fixing the type of `name` in `products.yaml`.

## Lab Rules
- Edit only `products.yaml`.

## Specmatic references
- Backward compatibility overview: [https://docs.specmatic.io/contract_driven_development/backward_compatibility](https://docs.specmatic.io/contract_driven_development/backward_compatibility)
- Backward compatibility rules: [https://docs.specmatic.io/contract_driven_development/backward_compatibility_rules](https://docs.specmatic.io/contract_driven_development/backward_compatibility_rules)

## Part A: Create the intentional breaking change
`products.yaml` currently matches the git-tracked baseline. Edit it so the new version becomes backward incompatible.

Change:

```yaml
info:
  version: 1.0.0
```

to:

```yaml
info:
  version: 1.1.0
```

Then under the `200` response schema for `GET /products/{id}`, change:

```yaml
name:
  type: string
```

to:

```yaml
name:
  type: number
```

and add:

```yaml
category:
  type: string
```

Your response schema should now have:

```yaml
properties:
  name:
    type: number
  sku:
    type: string
  category:
    type: string
```

You now have an uncommitted change in a tracked contract file. Specmatic will compare it to the version on `origin/main`.

## Part B: Run the backward compatibility check
Run:

```shell
docker run --rm \
  -v ..:/workspace \
  -v ../license.txt:/specmatic/specmatic-license.txt:ro \
  -w /workspace \
  specmatic/enterprise:latest \
  backward-compatibility-check \
  --base-branch origin/main \
  --target-path backward-compatibility-testing/products.yaml
```

Why the command is structured this way:
- `-v ..:/workspace` mounts the `labs` repository root, not just this lab folder, so Specmatic can access the git repository metadata.
- `--base-branch origin/main` tells Specmatic which tracked baseline to compare against.
- `--target-path backward-compatibility-testing/products.yaml` tells Specmatic to compare the working tree version of this file with the tracked version on `origin/main`.

Expected failure highlights:

```terminaloutput
The Incompatibility Report:

  In scenario "Get product by id. Response: Product details"
  API: GET /products/(id:number) -> 200

    >> RESPONSE.BODY.name

        This is number in the new specification response but string in the old specification
```

Expected verdict:

```terminaloutput
(INCOMPATIBLE) This spec contains breaking changes to the API
```

Why this fails:
- Adding optional `category` is safe.
- Changing `name` from `string` to `number` is a breaking change for existing consumers.

## Part C: Fix the contract
Open `products.yaml`.

Under the `200` response schema for `GET /products/{id}`, change:

```yaml
name:
  type: number
```

to:

```yaml
name:
  type: string
```

Keep the new `category` field.
Keep version `1.1.0`.

## Part D: Re-run the check
Run the same command again:

```shell
docker run --rm \
  -v ..:/workspace \
  -v ../license.txt:/specmatic/specmatic-license.txt:ro \
  -w /workspace \
  specmatic/enterprise:latest \
  backward-compatibility-check \
  --base-branch origin/main \
  --target-path backward-compatibility-testing/products.yaml
```

Expected passing output:

```terminaloutput
Verdict for spec /workspace/backward-compatibility-testing/products.yaml:
  (COMPATIBLE) The spec is backward compatible with the corresponding spec from origin/main
```

## Clean up
Restore the tracked file:

```shell
git restore products.yaml
```

## Optional extension
- Add a `WIP` tag to the `get` operation in `products.yaml` and re-run the check to see how Specmatic reports incompatible changes for APIs still in progress.
- Try a different additive change, such as adding another optional response field, and confirm that the check still passes.

## Common confusion points
- Running the command from another directory. The README assumes you are in `labs/backward-compatibility-testing`.
- Expecting Specmatic to compare two arbitrary files. In this lab it compares your working tree change to the tracked version on `origin/main`.
- Mounting only the current folder into Docker. Specmatic needs the `labs` repo root mounted so git metadata is available inside the container.

## What you learned
- Backward compatibility can be validated directly from API specifications.
- Specmatic uses git history to compare your proposed contract change against the tracked baseline on `origin/main`.
- Safe additive changes pass, while consumer-breaking schema changes are flagged before merge.
