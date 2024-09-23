import importlib
import os
from pathlib import Path

from flask import Blueprint
from flask_restx import Api

api_bp = Blueprint("api", __name__)

authorizations = {
    'apikey': {
        'type': 'apiKey',
        'in': 'header',
        'name': 'Authorization',
        'description': "Type in the *'Value'* input box below: **'Bearer &lt;access_token&gt;'** "
    },
}

api = Api(
    api_bp,
    authorizations=authorizations,
    security='apikey',
    title=f'{os.environ.get("APPNAME")} Rest API',
    version='1.0',
    description="Main routes."
)

modules = [
    name for name in os.listdir(".\\app\\api")
    if not os.path.isfile(name)
    and '__' not in name
    and os.path.exists(f'.\\app\\api\\{name}\\__init__.py')
    and '.' not in name and 'users' not in name
]

for i in modules:
    cls = getattr(importlib.import_module(f'.{i}.controller', package=__name__), 'api')
    api.add_namespace(cls)