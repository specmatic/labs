#!/bin/bash
set -euo pipefail

vault_token="$(cat /vault/agent-auth/token)" || return 1
vault_response="$(curl -fsS \
  -H "X-Vault-Token: ${vault_token}" \
  http://vault:8200/v1/secret/data/api-security-schemes)" || return 1

BASIC_AUTH_TOKEN="$(jq -er '.data.data.BASIC_AUTH_TOKEN' <<< "${vault_response}")" || return 1
API_KEY="$(jq -er '.data.data.API_KEY' <<< "${vault_response}")" || return 1

export BASIC_AUTH_TOKEN
export API_KEY

unset vault_response vault_token
