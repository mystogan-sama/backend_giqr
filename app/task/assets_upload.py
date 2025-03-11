import copy
import os

import cloudinary.api
import cloudinary.uploader
import requests
import sqlalchemy
from flask import request, jsonify
from flask_jwt_extended import jwt_required
from flask_restx import Namespace, fields
from flask_restx import Resource
from marshmallow import Schema, fields as fields2
from marshmallow.validate import Length

from app import db
from app.utils import logger, message, internal_err_resp, \
    get_model, error_response


class AssetsUploadSchema(Schema):
    email = fields2.Email(required=True, validate=[Length(max=64)])


class AssetsUploadDto:
    api = Namespace("assets_upload", description="assets_upload_operations.")
    request_payload = api.model(
        "assets_upload_request_payload",
        {
            "email": fields.String(required=True),
        },
    )
    response = api.model(
        "assets_upload_response_data",
        {
            "status": fields.Boolean,
            "message": fields.String,
        },
    )


api = AssetsUploadDto.api
schema = AssetsUploadSchema()


@api.route("", endpoint='assets_upload')
class AssetsUpload(Resource):
    # @auth_internal_header()
    # @token_required
    def post(self):
        success_resp = 'UPLOAD ASSETS CLOUDINARY VIA SSO SUCCESS'
        failed_resp = 'UPLOAD ASSETS CLOUDINARY VIA SSO FAILED!'
        try:
            payload = request.form.to_dict(flat=True)
            fileParse = []
            for key in request.files.keys():
                fileParse.append((key, (request.files[key].filename, request.files[key].read(), request.files[key].content_type)))
            url = f'{os.environ.get("SSO_URL")}/internal/assets_upload'
            # url = 'http://localhost:5001/internal/assets_upload'
            # logger.debug(f'assets_upload to sso {url} begin ....')
            req = requests.post(url, headers={
                "Origin": request.origin,
                "Authorization": request.headers['Authorization'],
            }, files=fileParse, data=payload)
            if req.status_code != 200:
                logger.error(f'assets_upload to sso {url} FAILED!!!')
                logger.error(f'Response From sso => {str(req.status_code)} {req.reason} {req.json()}')
                response = jsonify(req.json())
                response.status_code = req.status_code
                return response
            logger.debug(f'assets_upload to sso {url} success')
            responseJson = req.json()
            # print(responseJson)
            if responseJson:
                table_id = copy.copy(payload['table_id'])
                model = get_model(db, payload['table_name'])

                if 'file_path' in responseJson['data']:
                    with db.engine.begin() as conn:
                        table = model.__table__
                        update = sqlalchemy.update(table).filter_by(id=int(table_id)).values(**responseJson['data']['file_path'])
                        conn.execute(update)
            resp = message(True, success_resp)
            return resp, 200
        except Exception as e:
            # print('ValueError')
            logger.error(e)
            return error_response(failed_resp, 500)

    @jwt_required()
    def delete(self):
        req_payload = request.get_json()
        cloudinary_path = req_payload['cloudinary_path']
        multiple_delete = req_payload['multiple_delete'] if 'multiple_delete' in req_payload else None
        success_resp = 'DELETE ASSETS CLOUDINARY SUCCESS'
        failed_resp = 'DELETE ASSETS CLOUDINARY FAILED!'
        try:
            if not multiple_delete:
                deleteResource = cloudinary.api.delete_resources([cloudinary_path['file']])
                if deleteResource['deleted'][cloudinary_path['file']] != 'deleted':
                    err = message(False, "Something went wrong during the process!")
                    err["error_reason"] = deleteResource
                    return err, 500

                delete = cloudinary.api.delete_folder(cloudinary_path['folder'])
                if not delete['deleted']:
                    err = message(False, "Something went wrong during the process!")
                    err["error_reason"] = delete
                    return err, 500

                resp = message(True, success_resp)
                return resp, 200
            else:
                deleteResource = cloudinary.api.delete_resources(cloudinary_path['file'])
                if 'deleted' not in deleteResource['deleted'].values():
                    err = message(False, "Something went wrong during the process!")
                    err["error_reason"] = deleteResource
                    return err, 500

                for row in cloudinary_path['folder']:
                    delete = cloudinary.api.delete_folder(row)
                    if not delete['deleted']:
                        print(row)
                        err = message(False, "Something went wrong during the process!")
                        err["error_reason"] = delete
                        return err, 500
                    resp = message(True, success_resp)
                    return resp, 200
        except Exception as e:
            logger.error(e)
            logger.error(failed_resp)
            return internal_err_resp()