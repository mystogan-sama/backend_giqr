import json
import os
import re
from functools import wraps
from flask import _request_ctx_stack
import requests
from flask import request, jsonify
from sqlalchemy.orm import with_loader_criteria
from werkzeug.local import LocalProxy
from sqlalchemy import inspect
from app import db
from app.utils import logger, get_model

current_user = LocalProxy(lambda: get_current_user())


def check_unit_privilege_on_read_db(orm_execute_state, member_of_list, modelName):
    # print(member_of_list)
    if current_user['member_of_list']:
        if (
                orm_execute_state.is_select and
                not orm_execute_state.is_column_load and
                not orm_execute_state.is_relationship_load
        ):
            columns = orm_execute_state.statement.columns
            if 'id_unit' in columns.keys():
                orm_execute_state.statement = orm_execute_state.statement.options(
                    with_loader_criteria(modelName, modelName.id_unit.in_(member_of_list))
                )


def check_unit_and_employee_privilege_on_read_db(orm_execute_state, model):
    # if orm_execute_state.is_select:
    #     orm_execute_state.update_execution_options(populate_existing=True)
    #     col_descriptions = orm_execute_state.statement.column_descriptions
    #     if col_descriptions[0]['entity'] is model:
    #         columns = orm_execute_state.statement.columns
    #         if current_user:
    #             if 'id_unit' in columns.keys():
    #                 member_of_list = current_user['member_of_list']
    #                 if (
    #                         orm_execute_state.is_select and
    #                         not orm_execute_state.is_column_load and
    #                         not orm_execute_state.is_relationship_load
    #                 ):
    #                     columns = orm_execute_state.statement.columns
    #                     orm_execute_state.statement = orm_execute_state.statement.options(
    #                         with_loader_criteria(model, model.id_unit.in_(list(set(member_of_list))))
    #                     )
    #
    #             if 'id_employee' in current_user:
    #                 id_employee = current_user['id_employee']
    #                 if id_employee and 'isManager' in current_user:
    #                     if 'Id_Employee' in columns.keys() and not current_user['isManager']:
    #                         if (
    #                                 orm_execute_state.is_select and
    #                                 not orm_execute_state.is_column_load and
    #                                 not orm_execute_state.is_relationship_load
    #                         ):
    #                             columns = orm_execute_state.statement.columns
    #                             orm_execute_state.statement = orm_execute_state.statement.options(
    #                                 with_loader_criteria(model, model.Id_Employee == id_employee)
    #                             )
    if orm_execute_state.is_select:
        orm_execute_state.update_execution_options(populate_existing=True)
        col_descriptions = orm_execute_state.statement.column_descriptions
        if col_descriptions[0]['entity'] is model or col_descriptions[0]['name'] == 'count':
            columns = orm_execute_state.statement.columns
            if current_user:
                member_of_list = current_user['member_of_list'] if 'member_of_list' in current_user else None
                id_employee = current_user['id_employee'] if 'id_employee' in current_user else None
                isManager = current_user['isManager'] if 'isManager' in current_user else None
                if member_of_list:
                    if (
                            orm_execute_state.is_select and
                            not orm_execute_state.is_column_load
                            and not orm_execute_state.is_relationship_load
                    ):
                        if 'id_unit' in columns.keys() or 'id_unit' in model.__table__.columns:
                            # orm_execute_state.update_execution_options(populate_existing=True)
                            columns = orm_execute_state.statement.columns
                            orm_execute_state.statement = orm_execute_state.statement.options(
                                with_loader_criteria(model, model.id_unit.in_(member_of_list))
                            )
                if id_employee:
                    if ('Id_Employee' in columns.keys() or 'Id_Employee' in model.__table__.columns) and not isManager:
                        if (
                                orm_execute_state.is_select and
                                not orm_execute_state.is_column_load and
                                not orm_execute_state.is_relationship_load
                        ):
                            columns = orm_execute_state.statement.columns
                            orm_execute_state.statement = orm_execute_state.statement.options(
                                with_loader_criteria(model, model.Id_Employee == id_employee)
                            )


def check_unit_privilege_on_changes_db(mapper, connection, target, member_of_list):
    # print(member_of_list)
    if 'id_unit' in mapper.columns:
        if member_of_list and target.id_unit:
            # print(type(member_of_list), int(target.id_unit))
            try:
                if int(target.id_unit) not in member_of_list:
                    logger.error(f'you are not allowed to actions on id_unit {target.id_unit}')
                    raise ValueError(f'you are not allowed to actions on id_unit {target.id_unit}')
            except Exception as error:
                logger.error(error)
                raise ValueError(f'you are not allowed to actions on id_unit {target.id_unit}')


def insert_user_activity(data, access_token):
    url = f'{os.environ.get("SSO_URL")}api/userActivity'
    req = requests.post(
        url,
        headers={'Authorization': access_token, 'Origin': os.environ.get("DOMAIN")},
        json=data
    )
    if req.status_code != 200:
        logger.error('userActivity to sso FAILED! ' + str(req.status_code) + ' ' + req.reason + req.text)
    else:
        logger.debug('create userActivity to sso successed!')
    return True


def limit_read_by_unit(args, current_users, mainModel, select_query):
    return select_query


def auth_privilege(user_info):
    return user_info


def token_required(fn):
    @wraps(fn)
    def decorator(*args, **kwargs):
        url = f'{os.environ.get("SSO_URL")}token_verify'
        logger.debug(f'Verify token to sso : {url} begin ....')
        authorizationHeader = request.headers.get('Authorization')
        if not authorizationHeader:
            response = jsonify({'msg': 'Missing Authorization Header'})
            response.status_code = 401
            return response

        if 'Bearer ' not in authorizationHeader:
            response = jsonify({'msg': 'Authorization Header is Not Correct! Type in "Bearer {access_token}"'})
            response.status_code = 401
            return response

        try:
            headers = {
                "Authorization": authorizationHeader,
            }
            jsonPayload = {'x_endpoint': request.path, 'x_method': request.method}
            req = requests.post(url, headers=headers, json=jsonPayload)

            if req.status_code != 200:
                logger.error(f'Verify token to sso : {url} FAILED!!!')
                logger.error(f'Response From sso => {str(req.status_code)} {req.reason} {req.json()}')
                response = jsonify(req.json())
                response.status_code = req.status_code
                return response
            user_data = req.json()
            user_data['access_token'] = authorizationHeader
            user_data['origin'] = request.origin
            _request_ctx_stack.top.jwt_user = user_data
            logger.debug(f'Verify token to sso : {url} success')
            # kwargs['current_user'] = req.json()
        except:
            response = jsonify({'msg': 'Authorization Header is Not Correct! Type in "Bearer {access_token}"'})
            response.status_code = 401
            logger.error(f'Verify token to sso ( {url} ) FAILED!!!')
            return response

        return fn(*args, **kwargs)

    return decorator


def get_current_user():
    jwt_user_dict = getattr(_request_ctx_stack.top, "jwt_user", None)
    return jwt_user_dict


def domain_claims():
    url = f'{os.environ.get("SSO_URL")}domain_claims'
    logger.debug(f'Get domain claim to sso : {url} begin ....')
    domain = os.environ.get('DOMAIN')
    req = requests.post(url, headers={'Origin': domain})
    if req.status_code != 200:
        # response = jsonify(req.json())
        # response.status_code = req.status_code
        logger.error(f'Get domain claim to sso : {url} FAILED!!!')
        logger.error(f'Domain => {domain} => {str(req.status_code)} {req.reason}')
        # logger.error(f'{req.text}')
        logger.error(
            f'Domain Not Found In SSO!. Setup in .env file or contact sso administrator for domain registration')
        return {'msg': f'{req.reason}'}, req.status_code

    if data := req.json():
        os.environ['APPNAME'] = data['data']['app']['name'] or ""
        logger.debug(
            f'========================== This App Name is = {os.environ.get("APPNAME")} ==========================')
        os.environ['APPDESC'] = data['data']['app']['info'].get('description', '') or ""
        os.environ['APP_LOGO'] = data['data']['app']['logo'].get('appLogo', '') or ""
        # os.environ['APP_LOGO_BIG'] = data['data']['app']['logo']['appLogoBig'] or ""
        # os.environ['APP_LOGO_LIGHT'] = data['data']['app']['logo']['appLogoLight'] or ""
        # os.environ['APP_LOGO_LIGHT_BIG'] = data['data']['app']['logo']['appLogoLightBig'] or ""
    logger.debug(f'Get domain claim to sso : {url} success')
    return domain


def syncronize_resource():
    url = f'{os.environ.get("SSO_URL")}sync_resources'
    logger.debug(f'Syncronize {os.environ.get("APPNAME")} endpoints list to sso {url} begin ....')
    domain = os.environ.get('DOMAIN')
    from app.api import api
    list_endpoint = api.__schema__
    resource = []
    for path in list_endpoint['paths']:
        url_path = re.sub("[\{\{].*?[\}\}]", "", path)
        resource.append(url_path)
    req = requests.post(url, headers={'Origin': domain}, data=json.dumps(resource))
    if req.status_code != 200:
        logger.error(f'Syncronize {os.environ.get("APPNAME")} endpoints list to sso {url} FAILED!!!')
        logger.error(f'Response From sso => {str(req.status_code)} {req.reason} {req.json()}')
        response = jsonify(req.json())
        response.status_code = req.status_code
        return response
    logger.debug(f'Syncronize {os.environ.get("APPNAME")} endpoints list to sso {url} success')
    return domain

#
# def assets_upload_bridge(data, modelName=None):
#     # url = f'{os.environ.get("SSO_URL")}assets_upload'
#     url = 'http://localhost:5000/internal/assets_upload'
#     logger.debug(f'assets_upload to sso {url} begin ....')
#     req = requests.post(url, headers=data['headers'], files=data['files'], data=data['payload'])
#     if req.status_code != 200:
#         logger.error(f'assets_upload to sso {url} FAILED!!!')
#         logger.error(f'Response From sso => {str(req.status_code)} {req.reason} {req.json()}')
#         response = jsonify(req.json())
#         response.status_code = req.status_code
#         return response
#     logger.debug(f'assets_upload to sso {url} success')
#     responseJson = req.json()
#
#     if responseJson:
#         model = get_model(db, modelName)
#
#         if 'file_path' in responseJson['data'] and model:
#             select_query = model.query.filter_by(id=data['payload']['table_id']).first()
#             for row in list(responseJson['file_path'].keys()):
#                 setattr(select_query, row, responseJson['file_path'][row])
#             db.session.commit()
#     return True
#
#
# def assets_upload(data, modelName=None):
#     # url = f'{os.environ.get("SSO_URL")}assets_upload'
#     url = 'http://localhost:5001/internal/assets_upload'
#     logger.debug(f'assets_upload to sso {url} begin ....')
#     req = requests.post(url, headers=data['headers'], files=data['files'], data=data['payload'])
#     if req.status_code != 200:
#         logger.error(f'assets_upload to sso {url} FAILED!!!')
#         logger.error(f'Response From sso => {str(req.status_code)} {req.reason} {req.json()}')
#         response = jsonify(req.json())
#         response.status_code = req.status_code
#         return response
#     logger.debug(f'assets_upload to sso {url} success')
#     responseJson = req.json()
#
#     if responseJson:
#         model = get_model(db, modelName)
#
#         if 'file_path' in responseJson['data'] and model:
#             select_query = model.query.filter_by(id=data['payload']['table_id']).first()
#             for row in list(responseJson['file_path'].keys()):
#                 setattr(select_query, row, responseJson['file_path'][row])
#             db.session.commit()
#     return True