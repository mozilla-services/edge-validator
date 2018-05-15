# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
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
