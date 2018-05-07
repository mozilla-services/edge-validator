#!/bin/bash

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# sync.sh - Sync the local resources  with remote data sources.
# Created: 2018-05-03

set -euo pipefail

# TODO: dry-run option

# The environment must set up with the correct AWS credentials
SRC_DATA_BUCKET=${SOURCE_DATA_BUCKET:-"net-mozaws-prod-us-west-2-pipeline-analysis"}
SRC_DATA_PREFIX=${SOURCE_DATA_PREFIX:-"amiyaguchi/sanitized-landfill-sample/v1"}
MPS_ROOT=${MPS_ROOT:-"./mozilla-pipeline-schemas"}
OUTPUT_PATH=${OUTPUT_PATH:-"resources"}

data_path="${OUTPUT_PATH}/data"
schema_path="${OUTPUT_PATH}/schemas"

# Create the resource directory if not exists.
if [[ ! -d ${OUTPUT_PATH} ]]; then
    echo "Creating the resource path: ${OUTPUT_PATH}"
    mkdir ${OUTPUT_PATH}
fi

function sync_data {
    src_data_path="s3://${SRC_DATA_BUCKET}/${SRC_DATA_PREFIX}"
    
    # List all available json samples.
    # ex: amiyaguchi/sanitized-landfill-sample/v1/system_id=telemetry/doc_type=anonymous/*.json
    paths=$(
        aws s3 ls --recursive $src_data_path |  # recursively list all files 
        grep .json |                            # find leaf nodes containing sampled documents
        tr -s ' ' | cut -d ' ' -f4              # get the prefix for the json document
                                                # aws ls returns multiple spaces, so pass it through tr
    )

    echo "Updating local sampled data from ${src_data_path}"
    cache="${OUTPUT_PATH}/.metadata_cache"
    
    # Update local data with remote data. There will only be a single file per document type.
    for path in ${paths}; do
        # https://stackoverflow.com/a/4749368
        if [[ -e ${cache} ]]; then
            if grep -Fxq ${path} ${cache}; then
                echo "Skipping cached ${path}"
                continue
            fi
        fi

        system=`echo ${path} | cut -d'/' -f4 | cut -d'=' -f2`
        doc_type=`echo ${path} | cut -d'/' -f5 | cut -d'=' -f2`
        
        system_dir="${data_path}/${system}"
        filename="${doc_type}.batch.json"
        
        # make the system directory e.g. telemetry if not exists
        if [[ ! -d ${system_dir} ]]; then
           mkdir -p ${system_dir}
        fi

        # copy and overwrite any existing data
        aws s3 cp s3://${SRC_DATA_BUCKET}/${path} ${system_dir}/${filename}
    done

    # cache metadata
    echo ${paths} | tr ' ' '\n' > ${cache}
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
        pushd .; cd ${MPS_ROOT}
        git log -n 1
        popd
    fi
    
    cp --recursive ${src_schema_path} ${schema_path}
}

sync_data
sync_schema

