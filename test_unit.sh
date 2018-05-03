#!/bin/bash

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

