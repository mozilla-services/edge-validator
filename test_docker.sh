#!/bin/sh

IMAGE=${IMAGE:-"edge-validator:latest"}

container_id="$(docker run -tid $IMAGE)"
docker exec "${container_id}" pipenv run \
    python -m pytest --junitxml=junit.xml tests/

# https://circleci.com/docs/2.0/configuration-reference/#store_test_results
mkdir -p test-reports/pytest/
docker cp "${container_id}":/app/junit.xml test-reports/pytest/results.xml
docker stop "${container_id}"
