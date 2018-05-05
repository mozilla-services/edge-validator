import json
import os

from flask import Flask, request
from jsonschema import validate
from jsonschema.exceptions import ValidationError

app = Flask(__name__)

def load_data():
    """Load schemas into memory while taking advantage of data preloading.
    
    See https://stackoverflow.com/a/42440784
    """

    # https://firefox-source-docs.mozilla.org/toolkit/components/telemetry/telemetry/data/common-ping.html
    common_schema = {
            "properties": {
                "type": {"type": "string"},
                "id": {"type": "string"},
                "creationDate": {"type": "string"},
                "version": {"type": "integer"},
                },
            "required": ["type", "id", "creationDate", "version"],
            }

    # Schemas have a naming convention. See `sync.sh` for an example of the ingestion
    # submission format.
    telemetry_schemas = {}
    for root, dirs, files in os.walk("resources/schemas/telemetry"):
        for name in files:
            if not name.endswith(".schema.json"):
                continue
            with open(os.path.join(root, name), "r") as f:
                key = name.split(".schema.json")[0]
                telemetry_schemas[key] = json.load(f)
                print("Registered {} as '{}'".format(name, key))

    return common_schema, telemetry_schemas


@app.route('/', methods=['POST'])
def index():
    content = request.get_json()
    
    resp = ('OK', 200)
    try:
        validate(content, common_schema)
        key = "{}.{}".format(content["type"], content["version"])
        schema = telemetry_schemas[key]
        validate(content, schema)
    except (ValidationError, KeyError) as e:
        resp = ("BAD: {}".format(e.message), 400)
    return resp


common_schema, telemetry_schemas = load_data()

