# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
import os
import time
import requests
from subprocess import run

import click
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
                    },
                    "required": ["error_rate", "total", "time"]
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


def get_text(resp):
    if os.environ.get("EXTERNAL"):
        return resp.text
    else:
        return resp.data.decode('utf-8')


def validate_sample(namespace, name, messages):
    start = time.time()
    fail = 0
    doctype = name.split('.batch.json')[0]
    errors = {}
    for msg in messages:
        route = '/submit/{}/{}'.format(namespace, doctype)
        rv = client.post(route,
                         data=msg.encode('utf-8'),
                         content_type='application/json')
        is_failure = rv.status_code != 200
        if is_failure:
            fail += 1
            text = get_text(rv)
            errors[text] = errors.get(text, 0) + 1

    end = time.time()
    total = len(messages)
    err_rate = fail/float(total)*100
    result = {
        "{}.{}".format(namespace, doctype): {
            'error_rate': round(err_rate, 2),
            'total': total,
            'time': round(end-start, 2),
            'errors': errors or None
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


def report(data_path, report_path):
    test_results = {
        "results": {}
    }

    for root, _, files in os.walk(data_path):
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

    if report_path:
        try:
            validate = json.Validator(json.dumps(REPORT_SCHEMA))
            validate(json.dumps(test_results))
        except ValueError as error:
            print(error.args)
            exit(-1)

        os.makedirs(os.path.dirname(report_path), exist_ok=True)

        print("Writing to {}".format(report_path))
        with open(report_path, 'w') as f:
            json.dump(test_results, f)


@click.group()
def cli():
    pass


@cli.command()
@click.option('--data-path', type=click.Path(exists=True),
              default='resources/data')
@click.option('--report-path', type=click.Path(dir_okay=False))
def report_command(data_path, report_path):
    """Run an integration report against currently loaded schemas."""
    report(data_path, report_path)


def checkout_mps_tag(tag):
    run(["git", "submodule", "foreach", "git", "checkout", tag])


@cli.command()
@click.argument('tag-A')
@click.argument('tag-B')
@click.option('--data-path', type=click.Path(), default='resources/data')
@click.option('--report-path', type=click.Path(file_okay=False), required=True)
def compare(tag_a, tag_b, data_path, report_path):
    checkout_mps_tag(tag_a)
    report(data_path, os.path.join(report_path, "{}.report.json".format(tag_a)))

    checkout_mps_tag(tag_b)
    report(data_path, os.path.join(report_path, "{}.report.json".format(tag_b)))

    checkout_mps_tag("master")


if __name__ == '__main__':
    cli()
