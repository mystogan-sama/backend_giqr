import os
from datetime import timedelta

basedir = os.path.abspath(os.path.dirname(__file__))


class Config:
    # Change the secret key in production run.
    SECRET_KEY = os.environ.get("SECRET_KEY", os.urandom(24))
    DEBUG = False
    SKU_REG_DIGIT = os.environ.get("SKU_REG_DIGIT", 6)
    JWT_SECRET_KEY = os.environ.get("JWT_SECRET_KEY", os.urandom(24))
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(minutes=100)
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=30)
    DB_ACCESS_TOKEN_EXPIRES = timedelta(minutes=100)
    SWAGGER_UI_DOC_EXPANSION = 'list'
    SWAGGER_UI_REQUEST_DURATION = True
    SWAGGER_UI_OPERATION_ID = True


class DevelopmentConfig(Config):
    SECRET_KEY = os.environ.get("SECRET_KEY", os.urandom(24))
    DEBUG = True
    SKU_REG_DIGIT = os.environ.get("SKU_REG_DIGIT", 6)
    JSON_SORT_KEYS = False
    JSONIFY_PRETTYPRINT_REGULAR = True
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL", "sqlite:///" + os.path.join(basedir, "data-dev.sqlite")
    )
    SQLALCHEMY_BINDS = os.environ.get('DB_CONNECTIONS')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_RECORD_QUERIES = True
    SQLALCHEMY_ECHO = False
    JWT_SECRET_KEY = os.environ.get("JWT_SECRET_KEY", os.urandom(24))
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(minutes=100)
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=30)
    DB_ACCESS_TOKEN_EXPIRES = timedelta(minutes=100)
    SWAGGER_UI_DOC_EXPANSION = 'list'
    SWAGGER_UI_REQUEST_DURATION = True
    SWAGGER_UI_OPERATION_ID = True


class TestingConfig(Config):
    DEBUG = True
    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    PRESERVE_CONTEXT_ON_EXCEPTION = False
    SQLALCHEMY_TRACK_MODIFICATIONS = False


class ProductionConfig(Config):
    DEBUG = False
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL", "sqlite:///" + os.path.join(basedir, "data.sqlite")
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False


config_by_name = dict(
    development=DevelopmentConfig,
    testing=TestingConfig,
    production=ProductionConfig,
    default=DevelopmentConfig,
)