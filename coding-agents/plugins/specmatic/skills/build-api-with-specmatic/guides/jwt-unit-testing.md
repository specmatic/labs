# JWT verification and unit testing

Apply when the application verifies asymmetric JWT signatures. Derive the algorithm and required claim checks from
the brief, contracts and repository instructions.

## Configure and preserve

Load the verification public key as required by the brief and repository instructions; use a dependency-injection
boundary to supply separate keys to test instances. Preserve any supplied, default or preconfigured key, even if its filename contains `test`. Verification needs
the issuer's public key; the issuer's private key is needed only to sign tokens, not to verify supplied signed examples.

## Unit-test setup

Generate a separate test key pair using the runtime's supported cryptographic library. Keep generated keys in memory
or test-owned temporary files, and supply the public key through configuration scoped to the test instance. Use the
same signature-verification implementation as normal execution, without an authentication bypass.

Never overwrite application trust files or change supplied signed examples to match test keys. Keep generated keys
and test overrides out of application source, default configuration and normal startup; clean up temporary test files
and restore any process-level configuration changed by tests.

```text
Normal startup:
  application = createApplication(jwtPublicKey = suppliedPublicKey)

Unit-test setup:
  testKeys = generateKeyPair()
  testApplication = createApplication(jwtPublicKey = testKeys.publicKey)
  token = sign(validClaims, testKeys.privateKey)
  assert testApplication accepts token
```

## Verify

- If a supplied token fails verification, verify its signature directly against the unchanged supplied public key
  using the runtime's supported cryptographic library. Distinguish signature failure from claim validation and
  application key-loading/configuration errors. Do not infer that a token is invalid because its signing key is absent.
- Exercise real signature verification, including rejection of a token signed by an unrelated key, and the required
  claim checks.
- Confirm supplied/default trust material is unchanged against its original contents or recorded digest, and test
  overrides do not affect normal startup.
- Run contract tests with normal application configuration and supplied signed examples. Passing tests with generated
  unit-test keys does not prove compatibility with the application's configured trust key.
