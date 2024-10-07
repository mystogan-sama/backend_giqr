import decimal
import json
import math
from cgitb import text
from datetime import datetime


from flask import request, current_app, jsonify
from flask_restx import Resource, reqparse, inputs
from sqlalchemy import create_engine, exc
from sqlalchemy.orm import sessionmaker
from sqlalchemy.sql.elements import Null

from app.utils import GeneralGetList, \
    GeneralPost, GeneralDelete, GeneralGetById, GeneralPutById, GeneralDeleteById, generateDefaultResponse, message, \
    error_response, DateTimeEncoder, logger
from . import crudTitle, enabledPagination, respAndPayloadFields, fileFields, modelName, filterField
from .doc import doc
from .model import WEB_SERT
from .service import Service
from ... import internalApi_byUrl, db
from ...sso_helper import token_required, current_user

api = doc.api

parser = reqparse.RequestParser()
parser.add_argument('fetch_child', type=inputs.boolean, help='boolean input for fetch unit children', default=True)

parser.add_argument('sort', type=str, help='for sorting, fill with column name')
parser.add_argument('sort_dir', type=str, choices=('asc', 'desc'), help='fill with "asc" or "desc"')


#### LIST
@api.route("")
class List(Resource):
    if enabledPagination:
        parser.add_argument('page', type=int, help='page/start, fill with number')
        parser.add_argument('length', type=int, help='length of data, fill with number')
        parser.add_argument('search', type=str, help='for filter searching')
    if filterField:
        for row in filterField:
            parser.add_argument(
                f"{row.replace(':', '').replace('>', '').replace('<', '').replace('=', '').replace('!', '')}")

    #### GET
    @doc.getRespDoc
    @api.expect(parser)
    # @token_required
    def get(self):
        return GeneralGetList(doc, crudTitle, enabledPagination, respAndPayloadFields, Service, parser)


    #### POST SINGLE/MULTIPLE
    @doc.postRespDoc
    @api.expect(doc.default_data_response, validate=False)
    @token_required
    def post(self):
        return GeneralPost(doc, crudTitle, Service, request)

#### BY ID
@api.route("/<int:id>")
class ById(Resource):
    #### GET
    @doc.getByIdRespDoc
    @token_required
    def get(self, id):
        return GeneralGetById(id, doc, crudTitle, Service)

    #### PUT
    @doc.putRespDoc
    @api.expect(doc.default_data_response)
    @token_required
    def put(self, id):
        return GeneralPutById(id, doc, crudTitle, Service, request, modelName, current_user, fileFields,
                              internalApi_byUrl)
    
    #### DELETE
    @doc.deleteRespDoc
    @token_required
    def delete(self, id):
        return GeneralDeleteById(id, doc, crudTitle, Service, request, modelName, current_user, fileFields,
                                 internalApi_byUrl)

#### GET SUMMARY
@api.route("/summary")
class Summary(Resource):
    @doc.getSummaryRespDoc
    @token_required
    def get(self):
        try:
            args = parser.parse_args()
            resultData = Service.getSummary(args)
            # if not resultData:
            #     return error_response(generateDefaultResponse(crudTitle, 'get-sum', 500), 500)
            resp = message(True, generateDefaultResponse(crudTitle, 'get-sum', 200))
            resp['data'] = resultData
            return resp, 200
        except Exception as e:
            current_app.logger.error(e)
            return error_response(generateDefaultResponse(crudTitle, 'get-sum', 500), 500)