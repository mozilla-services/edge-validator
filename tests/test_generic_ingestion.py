# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
from uuid import uuid4

import pytest
import rapidjson as json

from .utils import GenericURISpec, build_route

@pytest.mark.parametrize("namespace, doctype, docversion, docid, expected", [
    ('testing', 'test', 1, str(uuid4()), 200),              # ok
    ('testing', 'test', 1, None, 200),                      # omit doc_id
    ('testing', 'test', 1, 'definitely-not-a-uuid', 404),   # invalid uuid docid
    ('testing', 'test', None, None, 200),                   # omit version
    ('testing', 'test', 999, None, 400),                    # nonexisting version
    ('testing', 'test', 'v1', None, 404),                   # bad version
    ('testing', None, None, None, 404),                     # omit type
    ('testing', 'test-nonexisting-doctype', 1, None, 400),  # nonexisting type
    ('test-nonexisting-namespace', 'test', 1, None, 400),   # nonexisting namespace
])
def test_generic_ingestion_ok(client, ping, namespace, doctype, docversion, docid, expected):
    spec = GenericURISpec(namespace=namespace,
                          doctype=doctype,
                          docversion=docversion,
                          docid=docid)
    rv = client.post(build_route(spec),
                     data=json.dumps(ping),
                     content_type='application/json')
    assert rv.status_code == expected
