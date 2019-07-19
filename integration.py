#!/usr/bin/env python

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import difflib
import importlib
import os
import time
from subprocess import run, PIPE

import click
import rapidjson as json
import requests

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


class Reporter(object):
    def __init__(self, is_external=None):
        self.is_external = is_external or os.environ.get("EXTERNAL")
        self.client = self._get_client()

    def _get_client(self):
        if self.is_external:
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
            import app
            importlib.reload(app)
            app.app.config['TESTING'] = True
            client = app.app.test_client()
        return client

    def get_text(self, resp):
        # the response is via `requests`
        if self.is_external:
            return resp.text
        # the response is via `flask.test_client`
        else:
            return resp.data.decode('utf-8')

    def validate_sample(self, namespace, doc_type, doc_version, messages):
        start = time.time()
        errors = {}
        for msg in messages:
            route = '/submit/{}/{}'.format(namespace, doc_type)
            if int(doc_version) > 0:
                route = '{}/{}'.format(route, doc_version)
            resp = self.client.post(route,
                                    data=msg.encode('utf-8'),
                                    content_type='application/json')
            is_error = resp.status_code != 200
            if is_error:
                text = self.get_text(resp)
                errors[text] = errors.get(text, 0) + 1

        end = time.time()
        error_count = sum(errors.values())
        total = len(messages)
        error_rate = error_count / float(total) * 100
        result = {
            "{}.{}.{}".format(namespace, doc_type, doc_version): {
                'error_count': error_count,
                'total': total,
                'error_rate': round(error_rate, 2),
                'time': round(end - start, 2),
                'errors': errors or None
            }
        }
        return result

    @staticmethod
    def display(result):
        for doc_type, metric in result.items():
            errors = metric['errors']
            is_missing = (
                errors and
                len(errors) == 1 and
                "Missing Schema" in list(errors.keys())[0]
            )
            print(
                "DocType: {:<50}"
                "ErrorRate: {:>5}\t"
                "Total: {:>4}\t"
                "Time: {:>.1f} seconds\t"
                    .format(doc_type,
                            "" if is_missing else metric['error_rate'],
                            metric['total'],
                            metric['time'])
            )

    @staticmethod
    def save(path, result):
        try:
            validate = json.Validator(json.dumps(REPORT_SCHEMA))
            validate(json.dumps(result))
        except ValueError as error:
            print(error.args)
            exit(-1)

        os.makedirs(os.path.dirname(path), exist_ok=True)

        print("Writing to {}".format(path))
        with open(path, 'w') as f:
            json.dump(result, f, indent=4, sort_keys=True)

    def run(self, data_path, report_path=None):
        test_results = {"results": dict()}

        # Use the most recent data
        date_like = [name for name in os.listdir(data_path) if name.isdigit()]
        if not date_like:
            raise RuntimeError("missing a data folder with submission date")

        submission_date = max(date_like)
        data_path = os.path.join(data_path, submission_date)

        for root, _, files in os.walk(data_path):
            for name in files:
                namespace = os.path.basename(root)
                try:
                    doc_type, doc_version = name.split('.batch.json')[0].split('.')
                except ValueError:
                    # the doc_type contains a period
                    continue

                filename = os.path.join(root, name)
                messages = []
                with open(filename, 'r') as f:
                    for line in f:
                        content = json.loads(line).get('content', {})
                        messages.append(content)

                try:
                    result = self.validate_sample(namespace, doc_type, doc_version, messages)
                except ValueError:
                    continue
                self.display(result)
                test_results["results"] = {**result, **test_results["results"]}

        if not test_results["results"]:
            raise ValueError("the result set is empty; try synchronizing data")

        if report_path:
            self.save(report_path, test_results)


class Environment(object):
    @staticmethod
    def checkout(rev):
        run(["git", "submodule", "foreach",
             "git", "checkout", rev])

    @staticmethod
    def current_revision():
        res = run(["git", "submodule", "foreach",
                   "git", "rev-parse", "--abbrev-ref", "HEAD"], stdout=PIPE)
        head = res.stdout.split()[-1]
        return head.decode('utf-8')

    @staticmethod
    def sync(env=os.environ):
        run(["bash", "sync.sh"], env=env)


def diff(json_a_path, json_b_path, output_path):
    # extract a subset
    def _transform(path):
        """The following jq expression can be used for document comparison

            jq \
                '.results | to_entries |
                map({doc_type: .key, error_rate: .value.error_rate})' \
            test-reports/dev.report.json
        """
        with open(path, 'r') as f:
            data = json.loads(f.read())
        subset = {}
        # iterate over the measurements and collect comparable stats
        for doc_type, measures in data['results'].items():
            subset[doc_type] = {
                'error_rate': measures['error_rate']
            }
        return json.dumps(subset, indent=4).splitlines(keepends=True)

    json_a = _transform(json_a_path)
    json_b = _transform(json_b_path)

    result = difflib.unified_diff(json_a, json_b)
    output = ''.join(result)
    print(output)

    print("Writing diff to {}".format(output_path))
    with open(output_path, 'w') as f:
        f.write(output)


@click.group(chain=True)
def integrate():
    """Tools for running a continuous schema integration loop."""
    pass


@integrate.command('sync', short_help="synchronize remote resources")
@click.option('--output-path', type=click.Path(file_okay=False),
              default='resources/',
              help="path to the application resource folder.")
@click.option('--include-data/--ignore-data',
              default=True,
              help="fetch sampled data from a remote, performed by default")
@click.option('--data-bucket', type=str,
              default='telemetry-parquet',
              help="location of the s3 bucket")
@click.option('--data-prefix', type=str,
              default='sanitized-landfill-sample/v3',
              help="location of the sanitized-landfill-sample dataset")
@click.option('--include-tests/--ignore-tests',
              default=True,
              help="add schemas from the testing directory")
@click.option('--schema-root', type=click.Path(exists=True),
              default='mozilla-pipeline-schemas',
              help="path to a copy of the mozilla-pipeline-schemas repository")
def sync_cmd(**kwargs):
    """Synchronize local resources with remote data sources.

    The sync command updates the application resource folder with data from
    external sources. These resources are used by both the edge-validator and
    the integration script.

    Updates to mozilla-pipeline-schemas should be synchronized for application
    visibility. Likewise, the integration report is tied closely with the
    sanitized landfill sample data set, which is updated on a daily basis.

    New external resources should be added to the synchronization process with
    a clear focus on reproducibility.
    """
    # Backwards compatibility layer for `sync.sh`
    options = {
        'SOURCE_DATA_BUCKET': kwargs['data_bucket'],
        'SOURCE_DATA_PREFIX': kwargs['data_prefix'],
        'MPS_ROOT': kwargs['schema_root'],
        'OUTPUT_PATH': kwargs['output_path'],
        'INCLUDE_DATA': "true" if kwargs['include_data'] else "false",
        'INCLUDE_TESTS': "true" if kwargs['include_tests'] else "false",
    }
    env = {**os.environ, **options}
    Environment.sync(env)


@integrate.command('report', short_help="collect metrics about errors in a data-set")
@click.option('--data-path', type=click.Path(exists=True),
              default='resources/data',
              help="path to the the application data resources")
@click.option('--report-path', type=click.Path(dir_okay=False),
              help="path to store reports")
def report_cmd(data_path, report_path):
    """Run an integration report against currently loaded schemas."""
    Reporter().run(data_path, report_path)


@integrate.command('compare', short_help="compare schema errors across two revisions")
@click.argument('rev-A')
@click.argument('rev-B')
@click.option('--data-path', type=click.Path(),
              default='resources/data',
              help="path to the application data resources")
@click.option('--report-path', type=click.Path(file_okay=False),
              required=True,
              help="path to store reports")
@click.option('--cache/--no-cache', default=True,
              help="utilize cached reports to speed up comparisons")
def compare_cmd(rev_a, rev_b, data_path, report_path, cache):
    """Compare the results of two revisions of `mozilla-pipeline-schemas`."""

    if os.environ.get("EXTERNAL"):
        err_msg = "EXTERNAL configuration is currently not supported"
        raise NotImplementedError(err_msg)

    def _run_report(rev):
        output_path = os.path.join(report_path, "{}.report.json".format(rev))

        # exit early if the report already been run and we are using the cache
        if os.path.exists(output_path) and cache:
            return output_path

        Environment.checkout(rev)
        Environment.sync()
        Reporter().run(data_path, output_path)

        return output_path

    # keep track of the current branch
    head = Environment.current_revision()

    rev_a_path = _run_report(rev_a)
    rev_b_path = _run_report(rev_b)

    diff_path = os.path.join(report_path, "{}-{}.diff".format(rev_a, rev_b))
    diff(rev_a_path, rev_b_path, diff_path)

    Environment.checkout(head)


if __name__ == '__main__':
    integrate()
