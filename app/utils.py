import ast
import decimal
import json
import locale
import logging
import os
import sys
from datetime import datetime, date
from threading import Thread

from flask.json import JSONEncoder
from flask_jwt_extended import decode_token
from flask_restx import fields, reqparse, inputs
from sqlalchemy import inspect, or_, func, desc
from colorlog import ColoredFormatter
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.sql.elements import Null
from werkzeug.datastructures import FileStorage

from app import db

appName = os.environ.get("APPNAME")
sso_url = os.environ.get('SSO_URL')
currentAppUrl = "http://localhost:5000"
appEmail = os.environ.get("EMAIL")
appEmailPassword = os.environ.get("EMAIL_PWD")
appFrontWebLogo = os.environ.get("PUBLIC_LOGO")
appFrontWebUrl = os.environ.get("PUBLIC_URL")
api_key_fcm = os.environ.get("APIKEY_FCM")


def setup_custom_logger():
    LOG_LEVEL = logging.DEBUG
    formatter = "  %(log_color)s%(asctime)s %(levelname)-8s%(reset)s | %(log_color)s%(message)s%(reset)s"
    formatterFile = logging.Formatter(fmt='%(asctime)s %(levelname)-8s %(message)s')

    handler = logging.FileHandler('app_log_all.log', mode='a')
    handler.setFormatter(formatterFile)
    handler.setLevel(LOG_LEVEL)

    screen_handler = logging.StreamHandler(stream=sys.stdout)
    screen_handler.setFormatter(ColoredFormatter(formatter))
    screen_handler.setLevel(LOG_LEVEL)

    log = logging.getLogger('werkzeug')
    log.setLevel(LOG_LEVEL)
    log.addHandler(handler)
    log.addHandler(screen_handler)
    return log


logger = setup_custom_logger()


def message(status, msg):
    response_object = {"status": status, "message": msg}
    return response_object


def message_pagination(status, msg, pagination_data):
    response_object = {
        "status": status,
        "message": msg,
        "page": pagination_data.page,
        "pages": pagination_data.pages,
        "per_page": pagination_data.per_page,
        "total": pagination_data.total,
        "has_next": pagination_data.has_next,
        "next_num": pagination_data.next_num,
        "prev_num": pagination_data.prev_num,
    }
    return response_object


def message_paginationEmpty(status, msg):
    response_object = {
        "status": status,
        "message": msg,
        "page": 1,
        "pages": 1,
        "per_page": 0,
        "total": 0,
        "has_next": False,
        "next_num": 0,
        "prev_num": 0,
    }
    return response_object


def validation_error(status, errors):
    response_object = {"status": status, "errors": errors}

    return response_object


def err_resp(msg, reason, code):
    err = message(False, msg)
    err["error_reason"] = reason
    return err, code


def error_response(msg, code):
    err = {"status": False, "message": msg}
    return err, code


def internal_err_resp():
    err = message(False, "Something went wrong during the process!")
    err["error_reason"] = "server_error"
    return err, 500


def messageResponse(status, msg, code):
    response_object = {"status": status, "message": msg}
    return response_object, code


def row2dict(row):
    d = {}
    for column in row.__table__.columns:
        ob = getattr(row, column.name)
        if isinstance(ob, decimal.Decimal):
            d[column.name] = float(ob)
        if isinstance(ob, datetime):
            d[column.name] = ob.isoformat()
            # d[column.name] = ob.strftime("%Y-%m-%d %H:%M")
        if isinstance(ob, date):
            d[column.name] = ob.isoformat()
        else:
            d[column.name] = ob

    return d


def genRecrusive(query, parent):
    parent['children'] = []
    for item in query:
        # print(item)
        if item['parent_id'] == parent['id']:
            parent['is_header'] = True
            parent['children'].append(item)
            genRecrusive(query, item)


def rupiah_format(angka, with_prefix=False, desimal=2):
    # print(angka)
    locale.setlocale(locale.LC_ALL, 'IND')
    # print(locale.currency(angka, grouping=True, symbol=""))
    rupiah = locale.format("%.*f", (2, angka), True)
    if with_prefix:
        return "Rp. {}".format(rupiah)
    return rupiah


class MyDateFormat(fields.Raw):
    def format(self, value):
        return value.strftime('%d-%m-%Y')


def formatResp(ob):
    if isinstance(ob, decimal.Decimal):
        return float(ob)
    elif isinstance(ob, datetime) or isinstance(ob, date):
        return ob.isoformat()
    elif str(type(ob)) == "<class 'datetime.time'>":
        return ob.strftime("%H:%M:%S")
    else:
        return ob


def genFormArgs(enabledPagination, respAndPayloadFields, fileFields, filterField):
    parser = reqparse.RequestParser()
    if enabledPagination:
        parser.add_argument('page', type=int, help='page/start, fill with number')
        parser.add_argument('length', type=int, help='length of data, fill with number')
        parser.add_argument('search', type=str, help='for filter searching')
    if 'parent_id' in respAndPayloadFields:
        parser.add_argument('flat_mode', type=inputs.boolean, default=False, help='flat response data')

    # default args
    parser.add_argument('fetch_child', type=inputs.boolean, help='boolean input for fetch unit children',
                        default=True)
    parser.add_argument('sort', type=str, help='for sorting, fill with column name')
    parser.add_argument('sort_dir', type=str, choices=('asc', 'desc'), help='fill with "asc" or "desc"')

    for argKey in respAndPayloadFields.keys():
        if argKey in filterField:
            # print(respAndPayloadFields[argKey], respAndPayloadFields[argKey].__dict__)
            typeArg = str
            if argKey in fileFields:
                typeArg = FileStorage
            else:
                if str(respAndPayloadFields[argKey]) in ['NullableInteger', 'Integer']:
                    typeArg = int
                elif 'Boolean' in str(respAndPayloadFields[argKey]):
                    typeArg = inputs.boolean

            if argKey != "id":
                parser.add_argument(
                    argKey,
                    # required=respAndPayloadFields[argKey].required,
                    type=typeArg,
                    location="files" if argKey in fileFields else "path" if argKey == "id" else "form"
                )
    return parser


class NullableString(fields.String):
    __schema_type__ = ['string', 'null']
    __schema_example__ = 'nullable string'


class NullableInteger(fields.Integer):
    __schema_type__ = ['integer', 'null']
    __schema_example__ = 1


def row2dict_same_api_res(self, restXModel):
    d = {}
    commonFieldCurrency = ['nilai', 'pagu', 'harga', 'price', 'lalu', 'sekarang']
    for c in self.__table__.columns:
        if c.name in restXModel.keys():
            columnName = c.name
            ob = getattr(self, columnName)
            if isinstance(ob, decimal.Decimal) and columnName.lower() in commonFieldCurrency:
                d[f'{columnName}_format'] = rupiah_format(ob)
            d[columnName] = formatResp(ob)

    for (k, v) in vars(self.__class__).items():
        columnName = k
        if (type(v) is property or type(v) is hybrid_property) and k in restXModel.keys():
            ob = getattr(self, columnName)
            if isinstance(ob, decimal.Decimal) and columnName.lower() in commonFieldCurrency:
                d[f'{columnName}_format'] = rupiah_format(ob)
            d[columnName] = formatResp(ob)
        # elif str(type(v)) == "<class 'sqlalchemy.orm.attributes.InstrumentedAttribute'>" and k in restXModel.keys():
        #     ob = getattr(self, columnName)
        #     d[columnName] = ob
    return d


def assetUploadDefReqData(request, modelName, current_user, id):
    return {
        "url": "assets_upload",
        "headers": {
            "Origin": os.environ.get('DOMAIN'),
            "Authorization": request.headers['Authorization']
        },
        "payload": {
            "callback_page": request.form.get("callback_page"),
            "storeName": request.form.get("storeName"),
            "origin_before": request.origin,
            "table_name": modelName,
            "table_id": id,
            "asset_title": modelName,
            "cloudinary_path": modelName,
            "id_user": current_user['id'],
            "files": []
        }
    }


# def row2dict_same_api_res(row, restXModel):
#     d = {}
#     for column in row.__table__.columns:
#         if restXModel.get(column.name):
#             ob = getattr(row, column.name)
#             if isinstance(ob, decimal.Decimal):
#                 if column.name.lower() in ['nilai', 'pagu', 'harga', 'price', 'lalu', 'sekarang']:
#                     d[f'{column.name}_format'] = rupiah_format(ob)
#                 d[column.name] = float(ob)
#             elif isinstance(ob, datetime) or isinstance(ob, date):
#                 d[column.name] = ob.isoformat()
#                 # d[column.name] = ob.strftime("%Y-%m-%d %H:%M")
#             else:
#                 d[column.name] = ob
#     for key, prop in inspect(row.__class__).all_orm_descriptors.items():
#         t = getattr(row, key)
#         # print(key)
#         # print(t, hasattr(t, '__table__'))
#         if hasattr(t, '__table__'):
#             for key2 in t.__mapper__.c.keys():
#                 # print(key2)
#                 for key3, prop3 in inspect(t.__class__).all_orm_descriptors.items():
#                     t2 = getattr(t, key3)
#                     if hasattr(t2, '__table__'):
#                         for key4 in t2.__mapper__.c.keys():
#                             if not key4.startswith('_') and restXModel.get(key4) and key4 != 'id':
#                                 ob3 = getattr(t, key4)
#                                 if isinstance(ob3, decimal.Decimal):
#                                     d[key4] = float(ob3)
#                                 elif isinstance(ob3, datetime) or isinstance(ob3, date):
#                                     d[key4] = ob3.isoformat()
#                                 else:
#                                     d[key4] = ob3
#
#                 try:
#                     if not key2.startswith('_') and restXModel.get(key2) and key2 != 'id':
#                         ob2 = getattr(row, key2)
#                         if isinstance(ob2, decimal.Decimal):
#                             d[key2] = float(ob2)
#                         elif isinstance(ob2, datetime) or isinstance(ob2, date):
#                             d[key2] = ob2.isoformat()
#                         else:
#                             d[key2] = ob2
#                 except Exception as e:
#                     print(e)
#                     # t2 = getattr(row, key2)
#                     # print(t2)
#                     print('key not exist')
#
#     return d


class JsonEncoder(JSONEncoder):
    def default(self, obj):
        # print('here...')
        if isinstance(obj, decimal.Decimal):
            # print('here')
            return float(obj)
        return JSONEncoder.default(self, obj)


class DateTimeEncoder(json.JSONEncoder):
    def default(self, o):
        try:
            if isinstance(o, datetime):
                # return o.isoformat()
                return o.strftime("%Y-%m-%d %H:%M")
            if isinstance(o, date):
                return o.isoformat()
                # return o.strftime("%Y-%m-%d")
            if isinstance(o, decimal.Decimal):
                return float(o)
                # return str(o)
            iterable = iter(o)
        except TypeError:
            pass
        else:
            return list(iterable)
        return json.JSONEncoder.default(self, o)


def keys_exists(element, *keys):
    """
    Check if *keys (nested) exists in `element` (dict).
    """
    if not isinstance(element, dict):
        raise AttributeError('keys_exists() expects dict as first argument.')
    if len(keys) == 0:
        raise AttributeError('keys_exists() expects at least two arguments, one given.')

    _element = element
    for key in keys:
        try:
            _element = _element[key]
        except KeyError:
            return False
    return True


class DictItem(fields.Raw):
    def output(self, key, obj, *args, **kwargs):
        try:
            dct = getattr(obj, self.attribute)
        except AttributeError:
            return {}
        return dct or {}


def generateDefaultDoc(api, default_response, crudName, method, docName=""):
    doc_title = ""
    if method == 'get-list-pagination':
        doc_title = f'Get List Pagination of {crudName}'
    if method == 'get-list':
        doc_title = f'Get List of {crudName}'
    if method == 'get':
        doc_title = f'Get Specific {crudName}'
    if method == 'post':
        doc_title = f'Create a New {crudName}'
    if method == 'put':
        doc_title = f'Update Specific {crudName}'
    if method == 'delete':
        doc_title = f'Delete Specific {crudName}'
    if method == 'delete-multi':
        doc_title = f'Delete Multiple {crudName} With Array of "id"'
    if method == 'get-sum':
        doc_title = f'Get Summary of {crudName}'

    defaultResponse = {
        200: generateDefaultResponse(crudName, method, 200, api, docName, default_response),
        400: generateDefaultResponse(crudName, method, 400, api, docName, default_response),
        500: generateDefaultResponse(crudName, method, 500, api, docName, default_response)
    }
    if method not in ['post', 'put']:
        del defaultResponse[400]
    respDoc = api.doc(
        doc_title,
        responses=defaultResponse
    )

    return respDoc


def generateDefaultResponse(crudName, method, code, api=None, docName="", default_data_response=None):
    response_msg = ""
    respDef = {
        "status": fields.Boolean(default=False),
        "message": fields.String(default=""),
    }

    if method == 'get-list-pagination':
        if code == 200:
            response_msg = f"{crudName} data sent"
            respDef["page"] = fields.Integer(default=1)
            respDef["pages"] = fields.Integer(default=200)
            respDef["per_page"] = fields.Integer(default=10)
            respDef["total"] = fields.Integer(default=2000)
            respDef["has_next"] = fields.Boolean(default=True)
            respDef["next_num"] = fields.Integer(default=2)
            respDef["prev_num"] = fields.Integer(default=1)
            respDef["data"] = fields.List(fields.Nested(default_data_response))
        if code == 500:
            response_msg = f"Failed to {method.replace('-', ' ')} {crudName}!"
    if method == 'get-list' or method == 'get' or method == 'get-sum':
        if code == 200:
            response_msg = f"{crudName} data sent"
            respDef['status'] = fields.Boolean(default=True)
            respDef["data"] = fields.List(
                fields.Nested(default_data_response)) if method == 'get-list' else fields.Nested(default_data_response)
        if code == 500:
            response_msg = f"Failed to {method.replace('-', ' ')} {crudName}!"
    if method == 'post':
        if code == 200:
            response_msg = f"{crudName} has been created"
            respDef['status'] = fields.Boolean(default=True)
            respDef["data"] = fields.Nested(default_data_response)
        if code == 500:
            response_msg = f"Failed to create {crudName}!"
        if code == 409:
            response_msg = f"Can't add because the same data already exists on {crudName}!"
    if method == 'put':
        if code == 200:
            response_msg = f"{crudName} has been updated"
            respDef['status'] = fields.Boolean(default=True)
            respDef["data"] = fields.Nested(default_data_response)
        if code == 500:
            response_msg = f"Failed to update {crudName}!"
        if code == 409:
            response_msg = f"Can't change because the same data already exists on {crudName}!"
    if method == 'delete':
        if code == 200:
            response_msg = f"{crudName} has been deleted"
            respDef['status'] = fields.Boolean(default=True)
            respDef["data"] = fields.Nested(default_data_response)
        if code == 500:
            response_msg = f"Failed to delete {crudName}!"
    if method == 'delete-multi':
        if code == 200:
            response_msg = f"{crudName} has been deleted"
            respDef['status'] = fields.Boolean(default=True)
            respDef["data"] = fields.List(fields.Nested(default_data_response))
        if code == 500:
            response_msg = f"Failed to delete {crudName}!"

    if code == 400:
        response_msg = f"Duplicate data! {crudName} unique fields is already being used."
    if code == 404:
        response_msg = f"{crudName} not found!"

    respDef["message"] = fields.String(default=response_msg)

    if api and docName != "":
        method = method.replace('-', '_')
        default_response = api.model(
            f"{docName}_{method}_response_{code}", respDef
        )
        return (response_msg, default_response)
    else:
        return response_msg


def get_or_create(session, model, defaults=None, **kwargs):
    instance = session.query(model).filter_by(**kwargs).first()
    if instance:
        return instance, False
    else:
        kwargs |= defaults or {}
        instance = model(**kwargs)
        try:
            session.add(instance)
            session.commit()
        except Exception:  # The actual exception depends on the specific database so we catch all exceptions. This is similar to the official documentation: https://docs.sqlalchemy.org/en/latest/orm/session_transaction.html
            session.rollback()
            instance = session.query(model).filter_by(**kwargs).first()
            return instance, False
        else:
            return instance, True


def getDatabaseSelectorUrl(request):
    if request.method != 'OPTIONS':
        dataYearArg = None

        token = request.headers.get('Authorization').replace('Bearer ', '').strip() if request.headers.get(
            'Authorization') else None
        if token:
            # print(decode_token(token))
            if decode_token(token)['dataYear']:
                dataYearArg = decode_token(token)['dataYear']

        elif request.get_json():
            dataYearArg = request.get_json()['dataYear'] if 'dataYear' in request.get_json() else None

        elif request.form:
            dataYearArg = request.form['dataYear'] if 'dataYear' in request.form else None

        elif request.args:
            dataYearArg = request.args['dataYear'] if 'dataYear' in request.args else None

        connection_map = ast.literal_eval(os.environ.get('DB_CONNECTIONS'))
        if dataYearArg:
            # print(f'dataYearArg: {dataYearArg}')
            if str(dataYearArg) not in connection_map.keys():
                connection_map[str(dataYearArg)] = str(connection_map['all']).replace('XXXX', str(dataYearArg))
                return connection_map[str(dataYearArg)]
            else:
                return connection_map[str(dataYearArg)]
        else:
            return connection_map['default']


def object_as_dict(obj):
    return {c.key: getattr(obj, c.key)
            for c in inspect(obj).mapper.column_attrs}


def isExist(data, mainModel, uniqueField):
    try:
        if data.get('id'):
            return mainModel.query.filter_by(id=data["id"]).first() or None
        else:
            dynUniqueOr = []
            if uniqueField != "" and len(uniqueField) > 0:
                for row in uniqueField:
                    if row in data:
                        dynUniqueOr.append(getattr(mainModel, row) == data[row])
            if dynUniqueOr:
                return mainModel.query.filter(or_(*dynUniqueOr)).first() or None
            else:
                return None

    except Exception as error:
        logger.error(error)
        return False


def get_model(db, name):
    # return db.Model.registry._class_registry.get(name, None)
    for c in db.Model.registry._class_registry.values():
        if hasattr(c, '__table__') and c.__table__.fullname == name:
            return c


def get_model_by_column(db, column_name):
    for t in db.Model.registry._class_registry.values():
        if hasattr(t, '__table__'):
            # print(t)
            columns = t.__table__.columns
            for c in list(dict(columns).keys()):
                # print(c)
                if c == column_name:
                    return t


def publics_to_dict(self) -> {}:
    dict_ = {}
    for key in self.__mapper__.c.keys():
        if not key.startswith('_'):
            dict_[key] = getattr(self, key)

    for key, prop in inspect(self.__class__).all_orm_descriptors.items():
        t = getattr(self, key)
        if hasattr(t, '__table__'):
            for key2 in t.__mapper__.c.keys():
                try:
                    if not key2.startswith('_'):
                        dict_[key2] = getattr(self, key2)
                except Exception as e:
                    print('key not exist')

        dict_[key] = getattr(self, key)
    # print(dict_)
    # for key, prop in inspect(self.__class__).all_orm_descriptors.items():
    # if isinstance(prop, sqlalchemy.prope):
    #     dict_[key] = getattr(self, key)
    return dict_


########################################################################
# CRUD HELPER CONTROLLER
def genFormArgs(respAndPayloadFields, fileFields):
    argsParser = reqparse.RequestParser()
    for argKey in respAndPayloadFields.keys():
        # print(respAndPayloadFields[argKey], respAndPayloadFields[argKey].__dict__)
        typeArg = str
        if argKey in fileFields:
            typeArg = FileStorage
        else:
            if str(respAndPayloadFields[argKey]) in ['NullableInteger', 'Integer']:
                typeArg = int
            elif 'Boolean' in str(respAndPayloadFields[argKey]):
                typeArg = inputs.boolean

        if argKey != "id":
            argsParser.add_argument(
                argKey,
                # required=respAndPayloadFields[argKey].required,
                type=typeArg,
                location="files" if argKey in fileFields else "path" if argKey == "id" else "form"
            )
        # print(argsParser)
    return argsParser


def GeneralGetList(doc, crudTitle, enabledPagination, respAndPayloadFields, Service, parser, asData=None):
    try:
        args = parser.parse_args()
        if enabledPagination:
            resultData = Service.getDataServerSide(args)
        else:
            resultData = Service.getDataAll(args)

        resp = None
        resultJson = []
        if not resultData:
            if asData:
                return resultJson
            resp = message(True, generateDefaultResponse(crudTitle, 'get-list', 200))
            resp['data'] = resultJson
            return resp, 200

        if enabledPagination:
            resp = message_pagination(True, generateDefaultResponse(crudTitle, 'get-list', 200), resultData)
            for row in resultData.items:
                resultJson.append(row2dict_same_api_res(row, doc.default_data_response))
        else:
            if 'parent_id' not in respAndPayloadFields or args['flat_mode']:
                resp = message(True, generateDefaultResponse(crudTitle, 'get-list', 200))
                for row in resultData:
                    resultJson.append(row2dict_same_api_res(row, doc.default_data_response))
            else:
                resp = message(True, generateDefaultResponse(crudTitle, 'get-list', 200))
                root = {'id': None}
                resultDataNew = []
                for val in resultData:
                    newRow = row2dict_same_api_res(val, doc.default_data_response)
                    newRow['expanded'] = True
                    newRow['checked'] = False
                    resultDataNew.append(newRow)
                genRecrusive(sorted(resultDataNew,
                                    key=lambda d: d[args['sort']] if args['sort'] else d['index'] if 'index' in d else d['code'] if 'code' in d else 0),
                             root)
                resultJson = root['children']

        if asData:
            return resultJson
        resp = message(True, generateDefaultResponse(crudTitle, 'get-list', 200))
        resp['data'] = resultJson
        return resp, 200
    except Exception as e:
        logger.error(e)
        return error_response(generateDefaultResponse(crudTitle, 'get-list', 500), 500)


def GeneralPost(doc, crudTitle, Service, request, args=None, asData=False):
    try:
        payLoad = (request.get_json() or request.form) if request else args

        if isinstance(payLoad, dict):
            if Service.isExist(payLoad):
                return error_response(generateDefaultResponse(crudTitle, 'post', 400), 400)

        resultData = Service.addData(payLoad)

        if not resultData:
            return error_response(generateDefaultResponse(crudTitle, 'post', 500), 500)

        if isinstance(resultData, str):
            if 'you are not allowed to actions' in str(resultData):
                return error_response(str(resultData), 403)
            else:
                return error_response(generateDefaultResponse(crudTitle, 'post', 409), 409)

        resp = message(True, generateDefaultResponse(crudTitle, 'post', 200))
        if isinstance(resultData, list):
            resultJsonMulti = []
            for row in resultData:
                resultJsonMulti.append(row2dict_same_api_res(row, doc.default_data_response))
            resp["data"] = resultJsonMulti
        else:
            resultJson = row2dict_same_api_res(resultData, doc.default_data_response)
            resp["data"] = resultJson
        if asData:
            return resultJson
        return resp, 200
    except Exception as e:
        logger.error(e)
        return error_response(generateDefaultResponse(crudTitle, 'post', 500), 500)


def GeneralDelete(crudTitle, Service, request, fileFields, modelName, current_user, internalApi_byUrl):
    try:
        payload = request.get_json()
        if not payload['id']:
            return error_response(generateDefaultResponse(crudTitle, 'delete', 500), 500)

        if not isinstance(payload['id'], list):
            return error_response(generateDefaultResponse(crudTitle, 'delete', 500), 500)

        if len(payload['id']) == 0:
            return error_response(generateDefaultResponse(crudTitle, 'delete', 500), 500)

        resultJson = Service.deleteMultipleData(payload['id'])

        if fileFields:
            fileParse = []
            for row in fileFields:
                for resultRow in resultJson:
                    if resultRow[row]:
                        filename = resultRow[row].split("/")[-1]
                        fileParse.append(filename)

            if len(fileParse) > 0:
                dataToTask = assetUploadDefReqData(request, modelName, current_user, str(payload['id']))
                dataToTask['payload']["files"] = fileParse
                thread = Thread(target=internalApi_byUrl, args=(dataToTask, sso_url, "delete",))
                thread.start()

        resp = message(True, generateDefaultResponse(crudTitle, 'delete', 200))
        resp["data"] = resultJson
        return resp, 200
    except Exception as e:
        logger.error(e)
        return error_response(generateDefaultResponse(crudTitle, 'delete', 500), 500)


def GeneralGetById(id, doc, crudTitle, Service):
    try:
        if not Service.isExist({'id': id}):
            return error_response(generateDefaultResponse(crudTitle, 'get', 404), 404)
        resultData = Service.getDataById(id)
        if resultData:
            resultJson = row2dict_same_api_res(resultData, doc.default_data_response)
            resp = message(True, generateDefaultResponse(crudTitle, 'get', 200))
            resp["data"] = resultJson
            return resp, 200
        elif len(resultData) == 0:
            resp = message(True, generateDefaultResponse(crudTitle, 'get', 200))
            resp["data"] = {}
            return resp, 200
        else:
            return error_response(generateDefaultResponse(crudTitle, 'get', 500), 500)
    except Exception as e:
        logger.error(e)
        return error_response(generateDefaultResponse(crudTitle, 'get', 500), 500)


def GeneralPutById(id, doc, crudTitle, Service, request, modelName, current_user, fileFields, internalApi_byUrl):
    try:
        jsonPayload = True if 'application/json' in request.content_type else False

        payload = request.get_json() if jsonPayload else request.files

        existData = Service.isExist({'id': id})
        if not existData:
            return error_response(generateDefaultResponse(crudTitle, 'put', 404), 404)
        oldData = row2dict(existData)

        dataToTask = assetUploadDefReqData(request, modelName, current_user, id)

        resultJson = []
        if jsonPayload:
            fileParse = []
            for row in payload.keys():
                if row in fileFields and payload[row] is None:
                    filename = oldData[row].split("/")[-1]
                    fileParse.append(filename)

            if len(fileParse) > 0:
                dataToTask['payload']["files"] = fileParse
                thread = Thread(target=internalApi_byUrl, args=(dataToTask, sso_url, "put",))
                # thread.daemon = True
                thread.start()
                # thread.join()

            resultData = Service.updateData(id, payload)

            if not resultData:
                return error_response(generateDefaultResponse(crudTitle, 'put', 500), 500)

            if isinstance(resultData, str):
                if 'you are not allowed to actions' in str(resultData):
                    return error_response(str(resultData), 403)
                else:
                    return error_response(generateDefaultResponse(crudTitle, 'put', 409), 409)

            resultJson = row2dict_same_api_res(resultData, doc.default_data_response)
        else:
            if payload:
                fileParse = []
                for key in payload.keys():
                    fileParse.append((key, (payload[key].filename, payload[key].read(), payload[key].content_type)))

                if len(fileParse) > 0:
                    dataToTask["files"] = fileParse
                    thread = Thread(target=internalApi_byUrl, args=(dataToTask, currentAppUrl,))
                    # thread.daemon = True
                    thread.start()
                    # thread.join()

        resp = message(True, generateDefaultResponse(crudTitle, 'put', 200))
        resp["data"] = resultJson
        return resp, 200
    except Exception as e:
        print('ValueError')
        logger.error(e)
        return error_response(generateDefaultResponse(crudTitle, 'put', 500), 500)


def GeneralDeleteById(id, doc, crudTitle, Service, request, modelName, current_user, fileFields, internalApi_byUrl):
    try:
        if not (oldData := Service.isExist({'id': id})):
            return error_response(generateDefaultResponse(crudTitle, 'delete', 404), 404)

        if fileFields:
            fileParse = []
            for row in fileFields:
                if row2dict(oldData)[row]:
                    filename = row2dict(oldData)[row].split("/")[-1]
                    fileParse.append(filename)

            if len(fileParse) > 0:
                dataToTask = assetUploadDefReqData(request, modelName, current_user, id)
                dataToTask['payload']["files"] = fileParse
                thread = Thread(target=internalApi_byUrl, args=(dataToTask, sso_url, "delete",))
                thread.start()

        resultData = Service.deleteData(id)
        if not resultData:
            return error_response(generateDefaultResponse(crudTitle, 'delete', 500), 500)

        resp = message(True, generateDefaultResponse(crudTitle, 'delete', 200))
        resp["data"] = resultData
        return resp, 200
    except Exception as e:
        logger.error(e)
        return error_response(generateDefaultResponse(crudTitle, 'delete', 500), 500)


# def GeneralGetSummary(crudTitle, Service, parser):
#     try:
#         args = parser.parse_args()
#         resultData = Service.getSummary(args)
#         if not resultData:
#             return error_response(generateDefaultResponse(crudTitle, 'get-sum', 500), 500)
#         resp = message(True, generateDefaultResponse(crudTitle, 'get-sum', 200))
#         resp['data'] = resultData
#         return resp, 200
#     except Exception as e:
#         logger.error(e)
#         return error_response(generateDefaultResponse(crudTitle, 'get-sum', 500), 500)


########################################################################
# CRUD HELPER SERVICE
def GeneralIsExistOnDb(uniqueField, model, data):
    if 'id' not in data:
        if not uniqueField or len(uniqueField) == 0:
            return False
    return isExist(data, model, uniqueField)


# def GeneralGetSummary(model, crudTitle, current_app, args):
#     try:
#         select_query = model.query
#         total_data = {
#             "title": f"Total {crudTitle}",
#             "count": select_query.with_entities(func.count(model.id)).scalar()
#         }
#         result = [total_data]
#         return result
#     except Exception as error:
#         current_app.logger.error(error)
#         return None


def GeneralGetDataAll(respAndPayloadFields, model, current_app, args, filterField):
    try:
        select_query = model.query
        dynModels = []
        # USER FILTERS
        filters = {}
        for var in filterField:
            column = var
            if ':' in var:
                column = var.split(":")[2] if len(var.split(":")) > 2 else var.split(":")[0]
                operator = var.split(":")[1]
                dbColumn = var.split(":")[0]
                if column in args and args[column] and column in respAndPayloadFields:
                    if str(type(getattr(model, column))) == "<class 'property'>":
                        dynModel = get_model_by_column(db, column)
                        if dynModel and dynModel not in dynModels:
                            dynModels.append(dynModel)
                            select_query = select_query.join(dynModel)

                    # print(column, dbColumn, operator, args[column])
                    if operator == "<=":
                        select_query = select_query.filter(
                            getattr(model, dbColumn) <= args[column]
                        )
                    elif operator == ">=":
                        select_query = select_query.filter(
                            getattr(model, dbColumn) >= args[column]
                        )
                    elif operator == "boolean":
                        if args[column] == "true":
                            select_query = select_query.filter(
                                getattr(model, dbColumn) != Null()
                            )
                        else:
                            select_query = select_query.filter(
                                getattr(model, dbColumn) == Null()
                            )
            else:
                if column in args and args[column] and column in respAndPayloadFields:
                    if str(type(getattr(model, column))) == "<class 'property'>":
                        modelRelStr = column.split("_")[0] if "_" in column else column
                        dynModel = get_model(db, modelRelStr)
                        if dynModel and dynModel not in dynModels:
                            dynModels.append(dynModel)
                            select_query = select_query.join(dynModel)
                            select_query = select_query.filter(
                                getattr(dynModel, column.replace(f"{modelRelStr}_", "")) == args[column])
                    else:
                        filters[column] = args[column]

        # for extra in extraFilters:
        #     if extra['fieldName'] in filters:
        #         del filters[extra['fieldName']]
        #     if 'join' in extra:
        #         select_query = select_query.join(extra['join'])
        #
        #     if 'model' in extra:
        #         if extra['model'] != model:
        #             extraValue = args[extra['fieldName']]
        #             if extra['filterType'] == 'boolean':
        #                 extraValue = True if extraValue == "true" else False
        #                 select_query = select_query.filter(getattr(extra['model'], extra['fieldName']) == extraValue)
        #             elif extra['filterType'] == 'null':
        #                 if extraValue == "true":
        #                     select_query = select_query.filter(getattr(extra['model'], extra['fieldName']) != Null())
        #                 else:
        #                     select_query = select_query.filter(getattr(extra['model'], extra['fieldName']) == Null())

        if len(filters) > 0:
            select_query = select_query.filter_by(**filters)

        if 'index' in respAndPayloadFields:
            select_query = select_query.order_by(model.index).all()
        elif 'code' in respAndPayloadFields:
            select_query = select_query.order_by(model.code).all()
        else:
            select_query = select_query.order_by(model.id.desc()).all()

        return select_query
    except Exception as error:
        current_app.logger.error(error)
        return None


def GeneralGetDataServerSide(model, searchField, respAndPayloadFields, sortField, db, current_app, args, filterField):
    # print(args)
    try:
        select_query = model.query

        # COLLECT JOINS
        # list_relationships = []
        dynModels = []
        # list_relations = inspect(model).relationships.items() or []
        # if list_relations:
        #     for row in list_relations:
        #         list_relationships.append(row[0])
        #         dynModels.append(get_model(db, row[0]))
        # print(list_relationships)

        # USER FILTERS
        filters = {}
        for var in filterField:
            column = var
            if ':' in var:
                column = var.split(":")[2] if len(var.split(":")) > 2 else var.split(":")[0]
                operator = var.split(":")[1]
                dbColumn = var.split(":")[0]
                if column in args and args[column] and column in respAndPayloadFields:
                    if str(type(getattr(model, column))) == "<class 'property'>":
                        dynModel = get_model_by_column(db, column)
                        if dynModel and dynModel not in dynModels:
                            dynModels.append(dynModel)
                            select_query = select_query.join(dynModel)
                    # print(column, dbColumn, operator, args[column])
                    if operator == "<=":
                        select_query = select_query.filter(
                            getattr(model, dbColumn) <= args[column]
                        )
                    elif operator == ">=":
                        select_query = select_query.filter(
                            getattr(model, dbColumn) >= args[column]
                        )
                    elif operator == "boolean":
                        print(args[column] )
                        if args[column] == "true":
                            select_query = select_query.filter(
                                getattr(model, dbColumn) is not None
                            )
                        else:
                            select_query = select_query.filter(
                                getattr(model, dbColumn) is None
                            )
            else:
                if column in args and args[column] and column in respAndPayloadFields:
                    if str(type(getattr(model, column))) == "<class 'property'>":
                        modelRelStr = column.split("_")[0] if "_" in column else column
                        dynModel = get_model(db, modelRelStr)
                        if dynModel and dynModel not in dynModels:
                            dynModels.append(dynModel)
                            select_query = select_query.join(dynModel)
                            select_query = select_query.filter(
                                getattr(dynModel, column.replace(f"{modelRelStr}_", "")) == args[column])
                    else:
                        filters[column] = args[column]
        # print(filters)
        # if len(filters) > 0:
        #     select_query = select_query.filter_by(**filters)

        # SEARCH
        dynSearch = []
        if args['search']:
            args['page'] = 1
            search = '%{0}%'.format(args['search'])
            for row in searchField:
                try:
                    if str(type(getattr(model, row))) == "<class 'property'>":
                        dynModel = get_model_by_column(db, row)
                        if dynModel and dynModel not in dynModels:
                            dynModels.append(dynModel)
                            select_query = select_query.join(dynModel)
                            dynSearch.append(getattr(dynModel, row).ilike(search))
                    else:
                        dynSearch.append(getattr(model, row).ilike(search))
                except Exception as e:
                    print(e)

        # SORT
        sort = model.index if 'index' in respAndPayloadFields else model.id

        if args['sort'] and args['sort'] in sortField:
            try:
                row = args['sort']
                if str(type(getattr(model, row))) == "<class 'property'>":
                    dynModel = get_model_by_column(db, row)
                    sort = getattr(dynModel, row)
                    if dynModel and dynModel not in dynModels:
                        dynModels.append(dynModel)
                        select_query = select_query.join(dynModel)
                else:
                    sort = getattr(model, row)
            except Exception as e:
                print(e)

            if args['sort_dir'] == "desc":
                sort = sort.desc()
            else:
                sort = sort.asc()
        else:
            sort = sort.desc()

        ################# APPLY FILTERS
        if len(filters) > 0:
            select_query = select_query.filter_by(**filters)

        ################# APPLY search
        if len(dynSearch) > 0:
            select_query = select_query.filter(or_(*dynSearch))

        ################# APPLY ORDER_BY
        select_query = select_query.order_by(sort)

        # PAGINATION
        page = args['page'] if args['page'] else 1
        length = args['length'] if args['length'] else 10
        lengthLimit = length if length < 101 else 100
        query_execute = select_query.paginate(page, lengthLimit, error_out=False)
        return query_execute
    except Exception as error:
        current_app.logger.error(error)
        return None


def GeneralGetDataById(id, model, current_app):
    try:
        select_query = model.query.filter_by(id=id)
        if not (data := select_query.first()):
            return []
        return data
    except Exception as error:
        current_app.logger.error(error)
        return None


def GeneralAddData(data, db, model, current_app):
    try:
        if isinstance(data, list):
            resultMulti = []
            for row in data:
                newRow = model(**row)
                db.session.add(newRow)
                db.session.flush()
                if newRow.id:
                    resultMulti.append(newRow)
            db.session.commit()
            return resultMulti
        else:
            newRecord = model(**data)
            db.session.add(newRecord)
            db.session.commit()
            if not newRecord.id:
                return None
            return newRecord

    except IntegrityError as error:
        print("Duplicate Data!")
        db.session.rollback()
        current_app.logger.error(error)
        return "Duplicate Data!"
    except ValueError as error:
        db.session.rollback()
        current_app.logger.error(error)
        return str(error)
    except Exception as error:
        db.session.rollback()
        current_app.logger.error(error)
        return None


def GeneralUpdateData(id, data, model, db, current_app):
    try:
        # Check not exist
        existData = model.query.filter_by(id=id).first()

        for row in list(data.keys()):
            setattr(existData, row, data[row])
        db.session.commit()

        return existData
    except Exception as error:
        db.session.rollback()
        current_app.logger.error(error)
        return None


def GeneralDeleteData(id, model, db, current_app, doc):
    try:
        oldData = db.session.query(model).filter(model.id == id).first()
        resultJson = row2dict_same_api_res(oldData, doc.default_data_response)
        existData = model.query.filter_by(id=id).first()
        db.session.delete(existData)
        db.session.commit()
        return resultJson
    except Exception as error:
        db.session.rollback()
        current_app.logger.error(error)
        return None


def GeneraldeleteMultipleData(ids, model, db, current_app, doc):
    try:
        if len(ids) == 0:
            return None
        existDatas = model.query.filter(model.id.in_(ids))
        oldDataJson = []
        for row in existDatas.all():
            oldDataJson.append(row2dict_same_api_res(row, doc.default_data_response))
            db.session.delete(row)
            db.session.flush()
        # existDatas.delete(synchronize_session=False)
        db.session.commit()
        return oldDataJson
    except Exception as error:
        db.session.rollback()
        current_app.logger.error(error)
        return None