#!/bin/bash

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

set -e -u -o pipefail
set -x

HOST=${HOST:-localhost}
PORT=${PORT:-5000}

endpoint=${HOST}:${PORT}

if [[ -z "resources/schema" ]]; then
    echo "Resources have not been set up. Run sync."
    exit 1
fi


function test {
    name=$1
    system=$2
    expect=$3
    data=$4

    resp=`echo "$data" | curl --silent \
        -H "Content-Type: application/json" \
        -X POST \
        -d @- \
        ${endpoint}/${system}` 
    
    if [[ ${resp} == ${expect}* ]]; then
        echo "PASSED: ${name}"
    else
        echo -e "FAILED: ${name}\tREASON: ${resp}"
    fi
}


function validate_telemetry_samples {
    filename=$1
    
    total=0
    fail=0

    for line in $(cat ${filename}); do
        total=$(( $total + 1 ))
        
        data=`echo ${line} | jq -rc .content || echo "{}"`
        result=`test ${filename} telemetry OK "${data}"`
        if [[ ${result} == "FAILED*" ]]; then
            fail=$(( $fail + 1 ))
        fi

    done

    error_rate=`echo "$fail/$total*100" | bc`
    echo -e "Error Rate: ${error_rate}%\tTotal: ${total}\t${filename}"
}

function report_telemetry_samples {
    for path in resources/data/telemetry/*; do
        validate_telemetry_samples ${path}
    done
}

test_ping='
{
    "type": "test",
    "id": "some-uuid-string",
    "creationDate": "2018-05-07T20:57:32.023Z",
    "version": 1,
    "payload": {
        "foo": true,
        "bar": 7,
        "baz": "today is sunny"
    }
}'

test "common ping okay"         testing OK  "$(echo "${test_ping}" | jq .)"
test "common ping omit type"    testing BAD "$(echo "${test_ping}" | jq 'del(.type)')"
test "ping omit payload"        testing BAD "$(echo "${test_ping}" | jq -r 'del(.payload)')"
test "ping omit not-required"   testing OK  "$(echo "${test_ping}" | jq -r 'del(.payload.baz)')"
test "ping omit required"       testing BAD "$(echo "${test_ping}" | jq -r 'del(.payload.foo)')"
test "ping required wrong type" testing BAD "$(echo "${test_ping}" | jq -r '.payload.bar |= "not an int"')"

report_telemetry_samples

