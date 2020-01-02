#!/bin/sh

IMAGE=${IMAGE:-"edge-validator:latest"}

report_path=$(pwd)/"test-reports"

# disable tests on CI by checking for this environment variable.
container_id="$(docker run \
    -v $GOOGLE_APPLICATION_CREDENTIALS:/tmp/credentials \
    -e GOOGLE_APPLICATION_CREDENTIALS=/tmp/credentials \
    -e CI=true \
    -tid $IMAGE)"
cleanup() {
    echo "Cleaning up!"
    docker stop "${container_id}"
}
trap cleanup EXIT


CMD=$1
REV_A=$2
REV_B=$3

# return code from docker command
retval=0

if [ "$CMD" = "test" ]; then
    docker exec "${container_id}" pytest --junitxml=test-reports/pytest/junit.xml tests/
    retval=$?
    docker cp "${container_id}":/app/test-reports .
elif [ "$CMD" = "compare" ]; then
    if [ -z "$GOOGLE_APPLICATION_CREDENTIALS" ]; then
        echo "Missing GOOGLE_APPLICATION_CREDENTIALS"
        exit 1
    fi
    if [ -z "$REV_A" ] || [ -z "$REV_B" ]; then
        echo "Missing arguments REV_A or REV_B!" 1>&2
        exit 1
    fi
    docker exec "${container_id}" ./integration.py sync compare --report-path test-reports $REV_A $REV_B
    retval=$?
    docker cp "${container_id}":/app/test-reports ${report_path}

    diff="${report_path}/${REV_A}-${REV_B}.diff"
    if [ -s ${diff} ]; then
        cat ${diff}
        echo "changes detected between revisions ${REV_A} and ${REV_B}"
        exit 1
    fi
else
    echo "missing 'test' or 'compare'"
    exit 1
fi

exit $retval
