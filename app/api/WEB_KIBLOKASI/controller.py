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
from .model import WEB_KIBLOKASI
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
        parser = reqparse.RequestParser()
        parser.add_argument('getLokasi', type=str, required=True, help='Your help message for getDaftAset')
        parser.add_argument('KDKIB', type=str)
        parser.add_argument('UNITKEY', type=str)
        parser.add_argument('ASETKEY', type=str)
        parser.add_argument('TAHUN', type=str)
        args = parser.parse_args()

        if args['getLokasi'] == '1' and args['KDKIB'] and args['UNITKEY']:
            sql_query = """EXEC GET_ASET_LOKASI @KDKIB = :kdkib, @UNITKEY=:unitkey"""
            # Menambahkan ASETKEY ke query jika tersedia
            if args['ASETKEY']:
                sql_query += """, @ASETKEY=:asetkey"""

            # Menambahkan TAHUN ke query jika tersedia
            if args['TAHUN']:
                sql_query += """, @TAHUN=:tahun"""

            # Menjalankan query dengan parameter yang sesuai
            result = db.session.execute(sql_query,
                                        {'kdkib': args['KDKIB'], 'unitkey': args['UNITKEY'], 'asetkey': args['ASETKEY'],
                                         'tahun': args['TAHUN']})
            rows = result.fetchall()

            data = [dict(row) for row in rows]

            for item in data:
                for key, value in item.items():
                    if isinstance(value, datetime):
                        item[key] = value.isoformat()
                    elif isinstance(value, decimal.Decimal):
                        item[key] = float(value)

            response = {
                "status": True,
                "message": "data sent",
                "page": 1,
                "pages": 1,
                "per_page": 10,
                "total": len(data),
                "has_next": False,
                "next_num": None,
                "prev_num": None,
                "data": data
            }

            return response, 200

        else:
            return {'message': 'Invalid parameters'}, 400

        #### POST SINGLE/MULTIPLE

    @doc.postRespDoc
    # @api.expect(doc.default_data_response, validate=False)
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