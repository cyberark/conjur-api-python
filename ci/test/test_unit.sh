#!/bin/bash -ex

CURRENT_DIR=$(pwd)

rm -rf coverage.xml

if [[ "$1" == "-l" ]]; then
  shift
  nose2 -v '!integration' --with-coverage $@
  exit 0
fi

$CURRENT_DIR/ci/test/build_test_container.sh

rm -rf $CURRENT_DIR/output/*
docker run --rm \
  -t \
  -e TEST_ENV=true \
  -v "$(pwd):/opt/conjur-api-python" \
  conjur-api-python-test \
  bash -c "nose2 -v -X -A '!integration' --config ./tests/unit_test.cfg --with-coverage $@"
