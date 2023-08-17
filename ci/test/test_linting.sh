#!/bin/bash -e

echo "Building test container..."
CURRENT_DIR=$(pwd)
"$CURRENT_DIR/ci/test/build_test_container.sh"

DISABLED_ERRORS="fixme"

echo "Checking linting..."
set -x
docker run \
  --rm \
  -t \
  -e TEST_ENV=true \
  -v "$(pwd):/opt/conjur-api-python" \
  conjur-api-python-test \
  bash -c "pylint -r n -f parseable --rcfile './ci/test/.pylintrc' --disable=$DISABLED_ERRORS './conjur_api'"

echo "Linting completed!"
