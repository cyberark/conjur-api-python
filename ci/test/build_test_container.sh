#!/bin/bash -e

docker build \
    --file ci/test/Dockerfile.test \
    --tag conjur-api-python-test \
    .
