# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import rapidjson as json
import pytest
from app import app


@pytest.fixture
def client():
    app.config['TESTING'] = True
    yield app.test_client()


@pytest.fixture
def ping():
    return {
        "type": "test",
        "id": "some-uuid-string",
        "creationDate": "2018-05-07T20:57:32.023Z",
        "version": 1,
        "payload": {
            "foo": True,
            "bar": 7,
            "baz": "today is sunny"
        }
    }


def test_server_mounts_testing_namespace(client, ping):
    rv = client.post('/testing',
                     data=json.dumps(ping),
                     content_type='application/json')
    assert rv.status_code == 200


def test_ping_omit_type(client, ping):
    del ping["type"]
    rv = client.post('/testing',
                     data=json.dumps(ping),
                     content_type='application/json')
    assert rv.status_code == 400


def test_ping_omit_payload(client, ping):
    del ping["payload"]
    rv = client.post('/testing',
                     data=json.dumps(ping),
                     content_type='application/json')
    assert rv.status_code == 400


def test_ping_omit_required(client, ping):
    del ping["payload"]["foo"]
    rv = client.post('/testing',
                     data=json.dumps(ping),
                     content_type='application/json')
    assert rv.status_code == 400


def test_ping_omit_optional(client, ping):
    del ping["payload"]["baz"]
    rv = client.post('/testing',
                     data=json.dumps(ping),
                     content_type='application/json')
    assert rv.status_code == 200


def test_ping_wrong_type(client, ping):
    ping["payload"]["baz"]
    rv = client.post('/testing',
                     data=json.dumps(ping),
                     content_type='application/json')
    assert rv.status_code == 200
