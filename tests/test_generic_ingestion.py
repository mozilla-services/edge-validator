# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
from uuid import uuid4

import rapidjson as json

from .utils import GenericURISpec, build_route


def test_generic_ingestion_ok(client, ping):
    spec = GenericURISpec(namespace='testing',
                          doctype='test',
                          docversion=1,
                          docid=str(uuid4()))
    rv = client.post(build_route(spec),
                     data=json.dumps(ping),
                     content_type='application/json')
    assert rv.status_code == 200


def test_generic_ingestion_omit_docid(client, ping):
    spec = GenericURISpec(namespace='testing',
                          doctype='test',
                          docversion=1,
                          docid=None)
    rv = client.post(build_route(spec),
                     data=json.dumps(ping),
                     content_type='application/json')
    assert rv.status_code == 200


def test_generic_ingestion_invalid_uuid_docid(client, ping):
    spec = GenericURISpec(namespace='testing',
                          doctype='test',
                          docversion=1,
                          docid='definitely-not-a-uuid')
    rv = client.post(build_route(spec),
                     data=json.dumps(ping),
                     content_type='application/json')
    assert rv.status_code == 404


def test_generic_ingestion_omit_version(client, ping):
    spec = GenericURISpec(namespace='testing',
                          doctype='test',
                          docversion=None,
                          docid=None)
    rv = client.post(build_route(spec),
                     data=json.dumps(ping),
                     content_type='application/json')
    assert rv.status_code == 200


def test_generic_ingestion_nonexisting_version(client, ping):
    spec = GenericURISpec(namespace='testing',
                          doctype='test',
                          docversion=999,
                          docid=None)
    rv = client.post(build_route(spec),
                     data=json.dumps(ping),
                     content_type='application/json')
    assert rv.status_code == 400


def test_generic_ingestion_bad_version(client, ping):
    spec = GenericURISpec(namespace='testing',
                          doctype='test',
                          docversion='v1',
                          docid=None)
    rv = client.post(build_route(spec),
                     data=json.dumps(ping),
                     content_type='application/json')
    assert rv.status_code == 404


def test_generic_ingestion_omit_type(client, ping):
    spec = GenericURISpec(namespace='testing',
                          doctype=None,
                          docversion=None,
                          docid=None)
    rv = client.post(build_route(spec),
                     data=json.dumps(ping),
                     content_type='application/json')
    assert rv.status_code == 404


def test_generic_ingestion_nonexisting_type(client, ping):
    spec = GenericURISpec(namespace='testing',
                          doctype='test-nonexisting-doctype',
                          docversion=1,
                          docid=None)
    rv = client.post(build_route(spec),
                     data=json.dumps(ping),
                     content_type='application/json')
    assert rv.status_code == 400


def test_generic_ingestion_nonexisting_namespace(client, ping):
    spec = GenericURISpec(namespace='test-nonexisting-namespace',
                          doctype='test',
                          docversion=1,
                          docid=None)
    rv = client.post(build_route(spec),
                     data=json.dumps(ping),
                     content_type='application/json')
    assert rv.status_code == 400
