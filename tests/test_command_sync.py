# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
import pytest
import docker
import os
import shutil
import subprocess
from pathlib import Path

TEST_ACCESS_KEY = "testing-id"
TEST_SECRET_KEY = "testing-key"

if os.environ.get("CI"):
    pytest.skip(
        "skipping sync tests on CI due to docker dependencies", allow_module_level=True
    )

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


def awscli(command, cwd=None):
    res = subprocess.run(
        ["bash", "-c", f"aws --endpoint-url http://localhost:9000 {command}"],
        stdout=subprocess.PIPE,
        env={
            "AWS_ACCESS_KEY_ID": TEST_ACCESS_KEY,
            "AWS_SECRET_ACCESS_KEY": TEST_SECRET_KEY,
        },
        cwd=cwd,
    )
    if not res.returncode == 0:
        raise RuntimeError(f"aws failed: {str(res)}")
    return res.stdout.decode("utf-8")


def upload_test_data(bucket, prefix, submission_date, namespace, doc_type, doc_version):
    test_sample = (
        Path(__file__).parent
        / "resources"
        / "data"
        / "testing"
        / "test"
        / "test.1.batch.json"
    )

    remote_path = (
        f"s3://{bucket}/{prefix}/"
        f"submission_date_s3={submission_date}/"
        f"namespace={namespace}/"
        f"doc_id={doc_type}/"
        f"doc_version={doc_version}/"
        "long-hash.json"
    )

    awscli(f"""s3 cp "{test_sample}" "{remote_path}" """)
    assert "long-hash.json" in awscli(f"s3 ls --recursive s3://{bucket}")
    print(awscli(f"""s3 cp "{remote_path}" -"""))


# directory depths d<k>
@pytest.mark.parametrize("prefix", ["d1/d2", "d1/d2/d3", "d1/d2/d3/d4"])
def test_synchronize_path_depth(minio, tmp_path, prefix):
    cwd = Path(__file__).parent

    bucket = "test-bucket"
    submission_date = "20181212"
    namespace = "testing"
    doc_type = "test"
    doc_version = "1"

    awscli(f"s3 mb s3://{bucket}")
    upload_test_data(bucket, prefix, submission_date, namespace, doc_type, doc_version)

    sync = cwd.parent / "sync.sh"
    assert sync.exists()

    # setup the test directory
    test_dir = tmp_path / "root"

    # move testing schemas into mozilla-pipeline-schemas
    shutil.copytree(
        str(cwd / "resources" / "schemas"),
        str(test_dir / "mozilla-pipeline-schemas" / "schemas"),
    )

    # run the synchronization script
    res = subprocess.run(
        [sync],
        env={
            "AWS_ACCESS_KEY_ID": TEST_ACCESS_KEY,
            "AWS_SECRET_ACCESS_KEY": TEST_SECRET_KEY,
            "SOURCE_DATA_BUCKET": bucket,
            "SOURCE_DATA_PREFIX": prefix,
            "ENDPOINT_URL": "http://localhost:9000",
            "INCLUDE_TESTS": "false",
            "DEBUG": "true",
        },
        cwd=test_dir,
    )
    assert res.returncode == 0

    # assert that files are being copied down correctly
    resource = test_dir / "resources"
    assert (resource / "schemas" / namespace / doc_type / "test.1.schema.json").exists()
    assert (
        resource
        / "data"
        / submission_date
        / namespace
        / f"{doc_type}.{doc_version}.batch.json"
    ).exists()


def test_synchronize_ignores_spaces_in_namespace(minio, tmp_path):
    cwd = Path(__file__).parent

    bucket = "test-bucket"
    prefix = "sample/v1"
    namespace = "testing"
    submission_date = "20181212"
    doc_type = "test"
    doc_version = "1"

    awscli(f"s3 mb s3://{bucket}")
    upload_test_data(bucket, prefix, submission_date, namespace, doc_type, doc_version)
    upload_test_data(bucket, prefix, submission_date, "name space", doc_type, doc_version)

    sync = cwd.parent / "sync.sh"
    assert sync.exists()

    # setup the test directory
    test_dir = tmp_path / "root"

    # move testing schemas into mozilla-pipeline-schemas
    shutil.copytree(
        str(cwd / "resources" / "schemas"),
        str(test_dir / "mozilla-pipeline-schemas" / "schemas"),
    )

    # run the synchronization script
    res = subprocess.run(
        [sync],
        env={
            "AWS_ACCESS_KEY_ID": TEST_ACCESS_KEY,
            "AWS_SECRET_ACCESS_KEY": TEST_SECRET_KEY,
            "SOURCE_DATA_BUCKET": bucket,
            "SOURCE_DATA_PREFIX": prefix,
            "ENDPOINT_URL": "http://localhost:9000",
            "INCLUDE_TESTS": "false",
            "DEBUG": "true",
        },
        cwd=test_dir,
    )
    assert res.returncode == 0

    resource = test_dir / "resources"
    assert os.listdir(resource / "data" / submission_date) == [namespace]
