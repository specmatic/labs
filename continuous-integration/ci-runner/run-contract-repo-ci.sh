#!/bin/sh

set -eu

WORKSPACE=/workspace
TEMP_REPO=/tmp/contract-repo

echo "==> Preparing simulated contract repository"
rm -rf "$TEMP_REPO"
mkdir -p "$TEMP_REPO/contracts"
cp -R "$WORKSPACE/baseline/contracts/." "$TEMP_REPO/contracts/"
cp "$WORKSPACE/.spectral.yaml" "$TEMP_REPO/.spectral.yaml"

cd "$TEMP_REPO"
git init -q
git config user.name "Specmatic CI Lab"
git config user.email "specmatic-ci-lab@example.com"
git checkout -b main >/dev/null
git add .
git commit -q -m "Baseline contracts"

git checkout -b ci-check >/dev/null
rm -rf "$TEMP_REPO/contracts"
mkdir -p "$TEMP_REPO/contracts"
cp -R "$WORKSPACE/contracts/." "$TEMP_REPO/contracts/"

echo "==> Linting contracts with Spectral"
spectral lint --ruleset .spectral.yaml contracts/*.yaml

echo "==> Validating external examples"
specmatic examples validate --specs-dir contracts

echo "==> Checking backward compatibility against baseline main branch"
specmatic backward-compatibility-check \
  --base-branch main \
  --target-path contracts | tee /tmp/backward-compatibility.log

if grep -q "(INCOMPATIBLE)" /tmp/backward-compatibility.log; then
  echo "Backward compatibility gate failed."
  exit 1
fi
