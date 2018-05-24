# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
import argparse
import os
import time
import requests

import rapidjson as json


REPORT_SCHEMA = {
    "type": "object",
    "properties": {
        "results": {
            "additionalProperties": {
                "doctype": {
                    "properties": {
                        "error_rate": {
                            "type": "number",
                            "minimum": 0,
                            "maximum": 100
                        },
                        "total": {
                            "type": "integer",
                            "minimum": 0
                        },
                        "time": {
                            "type": "number",
                            "minumum": 0
                        }
                    }
                }
            }
        }
    },
    "required": ["results"]
}


if os.environ.get("EXTERNAL"):
    host = os.environ.get("HOST", "localhost")
    port = os.environ.get("PORT", 5000)

    class Client:
        @staticmethod
        def post(route, data, content_type):
            headers = {'content-type': content_type}
            uri = "http://{}:{}{}".format(host, port, route)
            return requests.post(uri, data=data, headers=headers)

    client = Client()
else:
    from app import app
    app.config['TESTING'] = True
    client = app.test_client()


def validate_sample(namespace, name, messages):
    start = time.time()
    fail = 0
    doctype = name.split('.batch.json')[0]
    for msg in messages:
        route = '/submit/{}/{}'.format(namespace, doctype)
        rv = client.post(route,
                         data=msg.encode('utf-8'),
                         content_type='application/json')
        fail += int(rv.status_code != 200)
    end = time.time()
    total = len(messages)
    err_rate = fail/float(total)*100
    result = {
        "{}.{}".format(namespace, doctype): {
            'error_rate': round(err_rate, 2),
            'total': total,
            'time': round(end-start, 2)
        }
    }
    return result


def print_results(result):
    for doctype, metric in result.items():
        print(
            "ErrorRate: {:.2f}%\t"
            "Total: {}\t"
            "Time: {:.1f} seconds\t"
            "DocType: {}"
            .format(metric['error_rate'],
                    metric['total'],
                    metric['time'],
                    doctype)
        )


def report_telemetry(path, output=None):
    test_results = {
        "results": {}
    }
    for root, _, files in os.walk(path):
        for name in files:
            filename = os.path.join(root, name)
            messages = []
            with open(filename, 'r') as f:
                for line in f:
                    content = json.loads(line).get('content', {})
                    messages.append(content)
            namespace = os.path.basename(root)
            result = validate_sample(namespace, name, messages)
            print_results(result)
            test_results["results"] = {**result, **test_results["results"]}

    if output:
        try:
            validate = json.Validator(json.dumps(REPORT_SCHEMA))
            validate(json.dumps(test_results))
        except ValueError as error:
            print(error.args)
            exit(-1)

        os.makedirs(os.path.dirname(output), exist_ok=True)

        with open(output, 'w') as f:
            json.dump(test_results, f)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Run an integration report.')
    parser.add_argument('-f', '--file', type=str, default=None,
                        help='Path to store results as a file')

    args = parser.parse_args()
    report_telemetry('resources/data/', output=args.file)
