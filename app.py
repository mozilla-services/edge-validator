from flask import Flask, request
from jsonschema import validate
from jsonschema.exceptions import ValidationError

app = Flask(__name__)


@app.route('/', methods=['POST'])
def index():
    schema = {"properties": {"a": {"type": "integer"}}}
    content = request.get_json()
    
    resp = ('OK', 200)
    try:
        validate(content, schema)
    except ValidationError as e:
        resp = ("BAD: {}".format(e.message), 400)
    return resp

