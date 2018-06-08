#!/bin/sh

IMAGE=${IMAGE:-"edge-validator:latest"}

report_path=$(pwd)/"test-reports"

# Create the output report directory if not exits.
if [ ! -d "${report_path}" ]; then
    echo "Creating the report path: ${report_path}"
    mkdir -p "${report_path}"
fi

sudo chown -R 10001:10001 ${report_path}
cleanup() {
  # recover ownership of the report folder
  sudo chown -R $(id -u):$(id -g) ${report_path}
}
trap cleanup EXIT


CMD=$1
REV_A=$2
REV_B=$3


if [ "$CMD" = "test" ]; then
    docker run \
        -v ${report_path}:/app/test-reports \
        -it ${IMAGE} pipenv run \
        python -m pytest --junitxml=test-reports/pytest/junit.xml tests/
elif [ "$CMD" = "compare" ]; then
    if [ -z "$REV_A" ] || [ -z "$REV_B" ]; then
        echo "Missing arguments REV_A or REV_B!" 1>&2
        exit 1
    fi
    docker run \
        -e AWS_ACCESS_KEY_ID \
        -e AWS_SECRET_ACCESS_KEY \
        -v ${report_path}:/app/test-reports \
        -it ${IMAGE} \
        pipenv run ./integration.py sync compare --report-path test-reports $REV_A $REV_B

    diff="${report_path}/${REV_A}-${REV_B}.diff"
    if [ -s ${diff} ]; then
        cat ${diff}
        echo "changes detected between revisions ${REV_A} and ${REV_B}"
        exit 1
    fi
else
    echo "missing 'test' or 'compare'"
fi

