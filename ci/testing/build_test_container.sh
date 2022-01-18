#!/bin/bash -e

docker build \
  --file ci/testing/Dockerfile.test \
  --tag conjur-cli-python-test \

             .
