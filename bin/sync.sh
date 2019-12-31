#!/bin/bash

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# sync.sh - Sync the local resources  with remote data sources.
# Created: 2018-05-03

set -euo pipefail

if [[ ! -z ${DEBUG:-} ]]; then set -x; fi

# change into the project root
cd "$(dirname "$0")/.."

# The environment must set up with the correct AWS credentials
MPS_ROOT=${MPS_ROOT:-"./mozilla-pipeline-schemas"}
OUTPUT_PATH=${OUTPUT_PATH:-"resources"}
INCLUDE_DATA=${INCLUDE_DATA:-"true"}
INCLUDE_TESTS=${INCLUDE_TESTS:-"true"}

data_path="${OUTPUT_PATH}/data"
schema_path="${OUTPUT_PATH}/schemas"

# Create the resource directory if not exists.
if [[ ! -d "${data_path}" ]]; then
    echo "Creating the resource path: ${data_path}"
    mkdir -p "${data_path}"
fi

if [[ ! -d "${schema_path}" ]]; then
    echo "Creating the resource path: ${schema_path}"
    mkdir -p "${schema_path}"
fi

function sync_data {
    # Update local data with remote data. There will only be a single file per document type.
    bin/download-document-sample.py --output-path "${data_path}"
}

function sync_schema {
    src_schema_path="${MPS_ROOT}/schemas"
    
    if [[ ! -d ${src_schema_path} ]]; then
        echo "Missing schema folder at the root of ${MPS_ROOT}!"
        exit 1
    fi

    echo "Copying schemas from ${src_schema_path}"

    # print out branch information if applicable
    if [[ -e "${MPS_ROOT}/.git" ]]; then
        pushd .; cd "${MPS_ROOT}"
        git --no-pager log -n1
        popd
    fi

    rsync -avh "${src_schema_path}"/ "${schema_path}"/ --delete
}

function copy_test_schema {
    echo "Copying testing schemas"
    rsync -avh "tests/resources/schemas"/ "${schema_path}"/
}

sync_schema
if [[ "${INCLUDE_DATA}" == true ]]; then sync_data; fi
if [[ "${INCLUDE_TESTS}" == true ]]; then copy_test_schema; fi
