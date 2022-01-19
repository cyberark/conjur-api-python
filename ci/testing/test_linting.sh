#!/bin/bash -e

echo "Building test container..."
CURRENT_DIR=$(pwd)
$CURRENT_DIR/ci/testing/build_test_container.sh

DISABLED_ERRORS="fixme"

echo "Checking linting..."
set -x
docker run \
  --rm \
  -t \
  -e TEST_ENV=true \
  -v "$(pwd):/opt/conjur-api-python" \
  conjur-cli-python-test pylint -r n -f parseable --rcfile "./ci/testing/.pylintrc" --disable="$DISABLED_ERRORS" "./conjur_api"

echo "Linting completed!"
