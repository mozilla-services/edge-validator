#!/bin/sh

IMAGE=${IMAGE:-"edge-validator:latest"}

container_id="$(docker run -tid $IMAGE)"
docker exec "${container_id}" pipenv run \
    python -m pytest --junitxml=junit.xml tests/
mkdir -p test-reports
docker cp "${container_id}":/app/junit.xml test-reports/
docker stop "${container_id}"
