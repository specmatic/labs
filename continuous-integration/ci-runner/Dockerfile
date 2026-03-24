FROM node:20-alpine

RUN apk add --no-cache git openjdk17-jre bash

RUN npm install -g specmatic @stoplight/spectral-cli

COPY run-contract-repo-ci.sh /opt/ci/run-contract-repo-ci.sh

RUN chmod +x /opt/ci/run-contract-repo-ci.sh
