#!/bin/bash

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

set -euo pipefail

endpoint=localhost:5000

test() {
    data=$1
    expect=$2
    resp=`curl --silent \
        -H "Content-Type: application/json" \
        -X POST \
        -d "${data}" \
        ${endpoint}`
    
    if [[ ${resp} == ${expect}* ]]; then
        echo "passed: ${resp}"
    else
        echo "failed: ${resp}"
    fi
}

test '{"a": 10}' OK
test '{"a": "failure"}' BAD

