# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
from uuid import uuid4

import pytest
import rapidjson as json

from .utils import GenericURISpec, build_route


@pytest.fixture
def route():
    spec = GenericURISpec(namespace='testing',
                          doctype='test',
                          docversion=1,
                          docid=str(uuid4()))
    return build_route(spec)


def test_server_mounts_testing_namespace(client, ping, route):
    rv = client.post(route,
                     data=json.dumps(ping),
                     content_type='application/json')
    assert rv.status_code == 200


def test_ping_omit_payload(client, ping, route):
    del ping["payload"]
    rv = client.post(route,
                     data=json.dumps(ping),
                     content_type='application/json')
    assert rv.status_code == 400


def test_ping_omit_required(client, ping, route):
    del ping["payload"]["foo"]
    rv = client.post(route,
                     data=json.dumps(ping),
                     content_type='application/json')
    assert rv.status_code == 400


def test_ping_omit_optional(client, ping, route):
    del ping["payload"]["baz"]
    rv = client.post(route,
                     data=json.dumps(ping),
                     content_type='application/json')
    assert rv.status_code == 200


def test_ping_wrong_type(client, ping, route):
    ping["payload"]["baz"]
    rv = client.post(route,
                     data=json.dumps(ping),
                     content_type='application/json')
    assert rv.status_code == 200
