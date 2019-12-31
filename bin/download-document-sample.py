#!/usr/bin/env python3

"""Download samples of json documents from the decoded and error stream.
This is meant for integration testing, and is easily inspected through the
command-line. For example, to count the total number documents per group:

  cat document_sample.ndjson | \
  jq -rc '.attributeMap | [.document_namespace, .document_type, .document_version]' | \
  uniq -c

This script is modified from [1].

[1] https://github.com/mozilla/gcp-ingestion/blob/master/ingestion-beam/bin/download-document-sample.
"""

import argparse
import base64
import gzip
import json
import logging
import os
import time
import shutil

from google.cloud import bigquery

PROJECT_ROOT = os.path.realpath(
    os.path.join(os.path.dirname(os.path.realpath(__file__)), "..")
)

# formatted using the BigQuery console formatter
DOCUMENT_SAMPLE_QUERY = """
-- Create a PubSub compatible row with the most recent document samples that
-- have been decoded.
with most_recent_timestamp AS (
  SELECT
    MAX(submission_timestamp)
  FROM
    `moz-fx-data-shared-prod`.monitoring.document_sample_nonprod_v1
)
SELECT
  STRUCT( document_namespace,
    document_type,
    document_version ) AS attributeMap,
  payload
FROM
  `moz-fx-data-shared-prod`.monitoring.document_sample_nonprod_v1
WHERE
  document_decoded
  AND submission_timestamp = (SELECT * FROM most_recent_timestamp)
ORDER BY
  document_namespace,
  document_type,
  document_version
"""


def extract_samples():
    """A generator for a query on the document sample table."""
    client = bigquery.Client()
    query_job = client.query(DOCUMENT_SAMPLE_QUERY)
    for row in query_job:
        row_dict = dict(row.items())
        row_dict["payload"] = gzip.decompress(row_dict["payload"]).decode("utf-8")
        yield row_dict


def most_recent_date():
    """Returns the datestring of the most recent sample formatted as YYYYMMDD."""
    query = """
    SELECT DATE(MAX(submission_timestamp)) as date
    FROM `moz-fx-data-shared-prod`.monitoring.document_sample_nonprod_v1
    """
    client = bigquery.Client()
    query_job = client.query(query)
    return next(iter(query_job))["date"].strftime("%Y%m%d")


def write_samples(root, submission_date, documents):
    # this will overwrite the whole directory
    base = f"{root}/{submission_date}"
    if os.path.exists(base):
        shutil.rmtree(base)
    os.makedirs(base)
    for doc in documents:
        namespace = doc["attributeMap"]["document_namespace"]
        doc_type = doc["attributeMap"]["document_type"]
        doc_version = doc["attributeMap"]["document_version"]
        filename = f"{namespace}.{doc_type}.{doc_version}.ndjson"
        with open(f"{base}/{filename}", "a+") as fp:
            fp.write(f"{doc['payload']}\n")


def main(args):
    os.chdir(PROJECT_ROOT)
    start = time.time()
    # TODO: speed-up sync by avoiding overwrites
    write_samples(args.output_path, most_recent_date(), extract_samples())
    logging.info(f"Done in {time.time()-start} seconds!")


def parse_arguments():
    parser = argparse.ArgumentParser("download-document-sample")
    parser.add_argument("--output-path", default="resources/data")
    args = parser.parse_args()
    return args


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main(parse_arguments())
