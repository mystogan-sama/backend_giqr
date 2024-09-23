import os
from functools import wraps

from flask import request

from app.utils import internal_err_resp, logger, validation_error


def auth_internal_header():
    def wrapper(fn):
        @wraps(fn)
        def decorator(*args, **kwargs):
            if not request.headers['dev-apikey']:
                error = validation_error(False, 'dev-apikey header not valid!')
                return error, 401
            if request.headers['dev-apikey'] != os.environ.get('SECRET_KEY'):
                logger.error('dev-apikey header not valid!')
                error = validation_error(False, 'dev-apikey header not valid!')
                return error, 401
            return fn(*args, **kwargs)

        return decorator

    return wrapper