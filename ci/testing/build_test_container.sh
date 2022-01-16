#!/bin/bash -e

docker build -f ci/testing/Dockerfile.test \
             -t conjur-cli-python-test \
             .
