# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
from uuid import uuid4

import pytest
import rapidjson as json

from .utils import TelemetryURISpec, build_route


@pytest.fixture
def default_values():
    return {
        'namespace': 'testing',
        'docid': str(uuid4()),
        'doctype': 'test',
        'appName': 'Firefox',
        'appVersion': '61.0a1',
        'appUpdateChannel': 'nightly',
        'appBuildId': '20180328030202',
    }


def test_telemetry_ingestion_ok(client, ping, default_values):
    spec = TelemetryURISpec(**default_values)
    rv = client.post(build_route(spec),
                     data=json.dumps(ping),
                     content_type='application/json')
    assert rv.status_code == 200


def test_generic_ingestion_omit_routes(client, ping, default_values):
    for key in default_values.keys():
        # create a new dictionary with the single key nulled out
        overwritten_dict = {**default_values, **{key: None}}
        spec = TelemetryURISpec(**overwritten_dict)
        rv = client.post(build_route(spec),
                         data=json.dumps(ping),
                         content_type='application/json')
        assert rv.status_code != 200
