#!/bin/bash -e

echo "Building test container..."
CURRENT_DIR=$(pwd)
$CURRENT_DIR/ci/testing/build_test_container.sh

DISABLED_ERRORS="fixme"

echo "Checking linting..."
set -x
docker-compose run --rm \
  --no-deps \
  test \
  pylint -r n -f parseable --disable="$DISABLED_ERRORS" "./conjur_api"

echo "Linting completed!"
