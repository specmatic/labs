# Specmatic Sample Application to demonstrate OpenAPI Multiple Security Schemes Support
![Specmatic Sample Application to demonstrate OpenAPI OAuth2 security scheme support](assets/SpecmaticOAuth.gif)

This project demonstrates how to leverage OpenAPI specifications as a Contract Test with Specmatic when the specification includes multiple [security schemes](https://spec.openapis.org/oas/v3.0.1#security-scheme-object) to protect different endpoints based on HTTP methods.

The lab starts in an intentionally broken state. Your job is to observe the failures, understand how each auth mechanism is wired, and make the smallest fixes needed to get the contract tests passing again.

## Time required to complete this lab
10-15 minutes.

## Prerequisites
- Docker is installed and running.
- You are in `labs/api-security-schemes`.

## Architecture

- `Keycloak` acts as the OAuth2 authorization server for `POST` requests.
- `Order API` is the system under test and enforces:
  - OAuth2 + RBAC for `POST`
  - Basic Auth for `GET`
  - API key auth for `DELETE`

The application validates OAuth2 tokens by calling the ```spring.security.oauth2.resourceserver.jwt.issuer-uri``` url defined in the ```application.properties``` file.

## Security Schemes

The application uses three security schemes:

- **OAuth2 (POST endpoints)**: Requires a bearer token with the appropriate role.
- **Basic Authentication (GET endpoints)**: Requires valid username/password credentials.
- **API Key (DELETE endpoints)**: Requires a valid `X-API-Key` header.

The OpenAPI contract defines these schemes:

**1. POST endpoints with OAuth2** :
```yaml
  securitySchemes:
    oAuth2AuthCode:
      type: oauth2
      description: keycloak based oauth security example
      flows:
        authorizationCode:
          authorizationUrl: http://localhost:8083/realms/specmatic/protocol/openid-connect/auth
          tokenUrl: http://localhost:8083/realms/specmatic/protocol/openid-connect/token
          scopes:
            email: email
```

**2. GET endpoints with Basic Auth**:
```yaml
  securitySchemes:
    basicAuth:
      type: http
      scheme: basic
      description: Basic Authentication with username and password
```

**3. DELETE endpoints with API Key**:
```yaml
  securitySchemes:
    apiKeyAuth:
      type: apiKey
      in: header
      name: X-API-Key
      description: API Key based authentication
```

## Basic and API Key

Specmatic will check if these security schemes are defined in the ```specmatic.yaml``` configuration.  
If found, it will use the configured values; otherwise, it will auto-generate appropriate authentication headers.

The security schemes are defined in ```specmatic.yaml```:
```yaml
specs:
  - spec:
      id: orderApiSpec
      securitySchemes:
        basicAuth:
          type: basicAuth
          token: ${BASIC_AUTH_TOKEN:dXNlcjppbnZhbGlkcGFzcw==}
        apiKeyAuth:
          type: apiKey
          token: ${API_KEY:INVALID_APIKEY1234}
```

## OAuth with RBAC

Unlike the Basic Auth and API key schemes, OAuth is not configured here as a single static token value in [`specmatic.yaml`](specmatic.yaml).

Instead, the OAuth/RBAC `POST` examples under [`auth_examples/`](./auth_examples) use Specmatic `before` fixtures:
1. The `before` fixture calls the Keycloak token endpoint.
2. The fixture captures `access_token` as `ACCESS_TOKEN`.
3. The protected API request should use this captured token in the `Authorization` header.

This sample defines two roles: `users` and `admins`, Users can interact with the order `POST` endpoints, while admins can interact with the product `POST` endpoints.

## Lab Rules

- Do not edit `docker-compose.yaml`.
- Do not edit the specs checked out under `.specmatic/repos/labs-contracts/openapi/security/` in this lab.
- Edit only [`specmatic.yaml`](specmatic.yaml) and the example files under [`auth_examples/`](./auth_examples).

## Intentional Failure

This lab is intentionally broken in two places:
1. The static auth values in [`specmatic.yaml`](specmatic.yaml) are wrong for `Basic` and `apiKey` Schemes.
2. The [OAuth example](./auth_examples) files are missing the `Authorization` header in the `POST` requests

Because of that:
- Basic Auth and API key requests fail with invalid credentials
- OAuth `before` fixtures still run, but the protected `POST` requests do not send the fetched token

## Run the failing tests

From `labs/api-security-schemes`, run:

```shell
docker compose up specmatic-test --abort-on-container-exit
```

Expected failing result:

```terminaloutput
Tests run: 185, Successes: 152, Failures: 33, WIP: 0, Errors: 0
```

- The compose command exits with a non-zero code.
- Specmatic reports failures against secured endpoints.
- The failures include `401 Unauthorized` responses.

For Basic and API Key, the failures are due to:
- Invalid `APIKey` credentials
- Invalid `Basic` Auth credentials (should be valid base64 encoded credentials)

For the OAuth failures, look carefully at the logs:
- The `before` fixture should run
- The token fetch request to Keycloak should succeed
- However, the protected `POST` request will still fail because it is not using the captured token

Cleanup after each run:

```shell
docker compose down -v
```

## Your Task

### 1. Fix the static auth config in `specmatic.yaml`

Update the fallback values in [`specmatic.yaml`](specmatic.yaml):
- change `dXNlcjppbnZhbGlkcGFzcw==` to `dXNlcjpwYXNzd29yZA==`
- change `INVALID_APIKEY1234` to `APIKEY1234`

### 2. Restore the bearer token wiring in the OAuth examples

Inspect all `POST` examples under [`auth_examples/`](./auth_examples), including both success and forbidden variants.
In each request, add the `Authorization` header using the captured `ACCESS_TOKEN` from the `before` fixture:

```plaintext
"Authorization": "Bearer $(ACCESS_TOKEN)"
```

Alternatively, just run the following command:
```shell
docker run --rm --entrypoint bash -v "${PWD}:/usr/src/app" -w /usr/src/app specmatic/enterprise -lc 'sed -i "s#dXNlcjppbnZhbGlkcGFzcw==#dXNlcjpwYXNzd29yZA==#g; s#INVALID_APIKEY1234#APIKEY1234#g" specmatic.yaml; find auth_examples -type f -name "*.json" -print0 | while IFS= read -r -d "" file; do tmp="$(mktemp)"; jq --arg auth "Bearer \$(ACCESS_TOKEN)" "if ((.partial?[\"http-request\"]?.method? // \"\" | ascii_upcase) == \"POST\") then .partial[\"http-request\"].headers.Authorization = \$auth else . end" "$file" > "$tmp" && mv "$tmp" "$file"; done'
```

## Verify the fix

Re-run:

```shell
docker compose up specmatic-test --abort-on-container-exit
```

Expected result:

```terminaloutput
Tests run: 185, Successes: 185, Failures: 0, WIP: 0, Errors: 0
```

Cleanup after run:

```shell
docker compose down -v
```

Generated test reports:
- `build/reports/specmatic/test/html/index.html`

## Troubleshooting

- If Docker ports `8080` or `8083` are already in use, stop the conflicting process and try again.
- If containers from a previous run are still present, run `docker compose down -v` before retrying.
- If Keycloak takes a little longer to start, wait for the compose run to finish; the test container already includes readiness checks.
- If `GET` or `DELETE` requests still fail, re-check the Basic Auth and API key fallback values in [`specmatic.yaml`](specmatic.yaml).
- If the OAuth token request succeeds but the protected `POST` still fails, check whether the example request is missing the `Authorization` header.

## Next step
If you are doing this lab as part of an eLearning course, return to the eLearning site and continue with the next module.
