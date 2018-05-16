# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
from collections import namedtuple


GenericURISpec = namedtuple('GenericURISpec', [
    'namespace',
    'doctype',
    'docversion',
    'docid',
])


# See: https://docs.telemetry.mozilla.org/concepts/pipeline/http_edge_spec.html#postput-request
TelemetryURISpec = namedtuple('GenericURISpec', [
    'namespace',
    'docid',
    'doctype',
    'appName',
    'appVersion',
    'appUpdateChannel',
    'appBuildId'
])


def build_route(spec):
    # drop everything after the first None
    if None in spec:
        spec = spec[:spec.index(None)]
    return '/'.join(['/submit'] + list(map(str, spec)))
