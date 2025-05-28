#!/bin/bash -ex

CURRENT_DIR=$(pwd)

rm -rf coverage.xml

if [[ "$1" == "-l" ]]; then
  shift
  pytest -v -m "not integration" $@
  exit 0
fi

$CURRENT_DIR/ci/test/build_test_container.sh

rm -rf $CURRENT_DIR/output/*
docker run --rm \
  -t \
  -e TEST_ENV=true \
  -v "$(pwd):/opt/conjur-api-python" \
  conjur-api-python-test \
  bash -c "pytest -v -m 'not integration' $@"
