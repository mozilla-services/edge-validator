# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
import pytest
import docker
import subprocess
from pathlib import Path

TEST_ACCESS_KEY = "testing-id"
TEST_SECRET_KEY = "testing-key"


@pytest.fixture
def minio():
    client = docker.from_env()
    container = client.containers.run(
        "minio/minio:latest",
        "server data/",
        detach=True,
        environment={
            "MINIO_ACCESS_KEY": TEST_ACCESS_KEY,
            "MINIO_SECRET_KEY": TEST_SECRET_KEY,
        },
        ports={"9000/tcp": "9000"},
    )
    yield container
    container.stop()


def awscli(command):
    res = subprocess.run(
        ["aws", "--endpoint-url", "http://localhost:9000"] + command.split(),
        stdout=subprocess.PIPE,
        env={
            "AWS_ACCESS_KEY_ID": TEST_ACCESS_KEY,
            "AWS_SECRET_ACCESS_KEY": TEST_SECRET_KEY,
        },
    )
    return res.stdout


def test_containers(minio):
    bucket = "test-bucket"
    submission_date = "20181212"
    namespace = "testing"
    doc_id = "test"
    doc_version = "1"

    awscli(f"s3 mb s3://{bucket}")
    test_sample = (
        Path(__file__).parent
        / "resources"
        / "data"
        / namespace
        / doc_id
        / "test.1.batch.json"
    )

    remote_path = (
        f"s3://{bucket}/"
        f"submission_date_s3={submission_date}/"
        f"namespace={namespace}/"
        f"doc_id={doc_id}/"
        f"doc_version={doc_version}/"
        "long-meaningless-hash.json"
    )

    awscli(f"s3 cp {test_sample} {remote_path}")
    assert False
