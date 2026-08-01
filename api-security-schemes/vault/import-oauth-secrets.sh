#!/bin/bash
set -euo pipefail

vault_token="$(cat /vault/agent-auth/token)" || return 1
vault_response="$(curl -fsS \
  -H "X-Vault-Token: ${vault_token}" \
  http://vault:8200/v1/secret/data/api-security-schemes)" || return 1

KEYCLOAK_USER_USERNAME="$(jq -er '.data.data.KEYCLOAK_USER_USERNAME' <<< "${vault_response}")" || return 1
KEYCLOAK_USER_PASSWORD="$(jq -er '.data.data.KEYCLOAK_USER_PASSWORD' <<< "${vault_response}")" || return 1
KEYCLOAK_SERVICE_ACCOUNT_USERNAME="$(jq -er '.data.data.KEYCLOAK_SERVICE_ACCOUNT_USERNAME' <<< "${vault_response}")" || return 1
KEYCLOAK_SERVICE_ACCOUNT_PASSWORD="$(jq -er '.data.data.KEYCLOAK_SERVICE_ACCOUNT_PASSWORD' <<< "${vault_response}")" || return 1
SPECMATIC_CLIENT_KEYSTORE_PASSWORD="$(jq -er '.data.data.SPECMATIC_CLIENT_KEYSTORE_PASSWORD' <<< "${vault_response}")" || return 1
SPECMATIC_CLIENT_KEY_PASSWORD="$(jq -er '.data.data.SPECMATIC_CLIENT_KEY_PASSWORD' <<< "${vault_response}")" || return 1

export KEYCLOAK_USER_USERNAME
export KEYCLOAK_USER_PASSWORD
export KEYCLOAK_SERVICE_ACCOUNT_USERNAME
export KEYCLOAK_SERVICE_ACCOUNT_PASSWORD
export SPECMATIC_CLIENT_KEYSTORE_PASSWORD
export SPECMATIC_CLIENT_KEY_PASSWORD

unset vault_response vault_token
