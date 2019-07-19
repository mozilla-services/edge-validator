#!/bin/bash

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# sync.sh - Sync the local resources  with remote data sources.
# Created: 2018-05-03

set -euo pipefail

if [[ ! -z ${DEBUG:-} ]]; then set -x; fi

# The environment must set up with the correct AWS credentials
SRC_DATA_BUCKET=${SOURCE_DATA_BUCKET:?}
SRC_DATA_PREFIX=${SOURCE_DATA_PREFIX:?}
MPS_ROOT=${MPS_ROOT:-"./mozilla-pipeline-schemas"}
OUTPUT_PATH=${OUTPUT_PATH:-"resources"}
INCLUDE_DATA=${INCLUDE_DATA:-"true"}
INCLUDE_TESTS=${INCLUDE_TESTS:-"true"}

data_path="${OUTPUT_PATH}/data"
schema_path="${OUTPUT_PATH}/schemas"

# overwrite the endpoint for testing if a url is given
if [[ ! -z ${ENDPOINT_URL:-} ]]; then
    echo "Using endpoint url ${ENDPOINT_URL}"
    aws="aws --endpoint-url ${ENDPOINT_URL}"
else
    aws="aws"
fi

# Create the resource directory if not exists.
if [[ ! -d "${data_path}" ]]; then
    echo "Creating the resource path: ${data_path}"
    mkdir -p "${data_path}"
fi

if [[ ! -d "${schema_path}" ]]; then
    echo "Creating the resource path: ${schema_path}"
    mkdir -p "${schema_path}"
fi

function path_tail {
    # $1: path delimited by '/'
    # $2: number of elements to keep from the tail
    echo $(echo "$1" | rev | cut -d'/' -f-$2 | rev)
}

function get_path_value {
    # $1: path delimited by '/' with elements 'KEY=VALUE'
    # $2: index of value to parse from path
    echo $(echo "$1" | cut -d'/' -f$2 | cut -d'=' -f2)
}

function sync_data {
    src_data_path="s3://${SRC_DATA_BUCKET}/${SRC_DATA_PREFIX}"

    # Use only the most recent data
    recent_date=$(
        $aws s3 ls "${src_data_path}"/submission_date_s3= |  # list all dates
        grep -Eow '[0-9]+' |                                # extract words made of digits
        tail -n1                                            # take the most recent
    )
    src_data_path="${src_data_path}/submission_date_s3=${recent_date}/"

    # List all available json samples.
    # ex: sanitized-landfill-sample/v3/submission_date_s3=20181212/namespace=telemetry/doc_type=anonymous/doc_version=4/*.json
    paths=$(
        $aws s3 ls --recursive "$src_data_path" |   # recursively list all files
        tr -s ' ' |                                 # replace multiple spaces
        cut -d ' ' -f4 |                            # get the column with the path
        grep .json
    )

    echo "Updating local sampled data from ${src_data_path}"
    cache="${OUTPUT_PATH}/.metadata_cache"
    
    # Update local data with remote data. There will only be a single file per document type.
    for path in ${paths}; do
        # https://stackoverflow.com/a/4749368
        if [[ -e ${cache} ]]; then
            if grep -Fxq "${path}" "${cache}"; then
                echo "Skipping cached ${path}"
                continue
            fi
        fi

        # keep the last 5 components of the directory spec
        spec=$(path_tail ${path} 5)
        submission_date=$(get_path_value ${spec} 1)
        namespace=$(get_path_value ${spec} 2)
        doc_type=$(get_path_value ${spec} 3)
        doc_version=$(get_path_value ${spec} 4)

        namespace_dir="${data_path}/${submission_date}/${namespace}"
        filename="${doc_type}.${doc_version}.batch.json"
        
        # make the system directory e.g. telemetry if not exists
        if [[ ! -d "${namespace_dir}" ]]; then
           mkdir -p "${namespace_dir}"
        fi

        # copy and overwrite any existing data
        $aws s3 cp "s3://${SRC_DATA_BUCKET}/${path}" "${namespace_dir}/${filename}" || true
    done

    # cache metadata
    echo "${paths}" | tr ' ' '\n' > "${cache}"
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
