#!/bin/sh

IMAGE=${IMAGE:-"edge-validator:latest"}

report_path=$(pwd)/"test-reports"

container_id="$(docker run -e AWS_ACCESS_KEY_ID -e AWS_SECRET_ACCESS_KEY -tid $IMAGE)"
cleanup() {
    docker stop "${container_id}"
}
trap cleanup EXIT


CMD=$1
REV_A=$2
REV_B=$3


if [ "$CMD" = "test" ]; then
    docker exec "${container_id}" pipenv run \
        python -m pytest --junitxml=test-reports/pytest/junit.xml tests/
    docker cp "${container_id}":/app/test-reports .
elif [ "$CMD" = "compare" ]; then
    if [ -z "$REV_A" ] || [ -z "$REV_B" ]; then
        echo "Missing arguments REV_A or REV_B!" 1>&2
        exit 1
    fi
    docker exec "${container_id}" pipenv run \
        ./integration.py sync compare --report-path test-reports $REV_A $REV_B
    docker cp "${container_id}":/app/test-reports ${report_path}

    diff="${report_path}/${REV_A}-${REV_B}.diff"
    if [ -s ${diff} ]; then
        cat ${diff}
        echo "changes detected between revisions ${REV_A} and ${REV_B}"
        exit 1
    fi
else
    echo "missing 'test' or 'compare'"
fi
