import os
from flask import Blueprint
from flask_restx import Api

from app.task.assets_upload import api as assets_upload_ns

internal_bp = Blueprint("internal", __name__)

authorizations = {
            'apikey': {
                'type': 'apiKey',
                'in': 'header',
                'name': 'Apikey',
                'description': "Type in the *'Value'* input box below: **'&lt;apikey&gt;'**"
            }
        }

internal = Api(internal_bp,
               title=f'{os.environ.get("APPNAME")} Internal API',
               description="For Internal routes.")

# API namespaces
internal.add_namespace(assets_upload_ns)