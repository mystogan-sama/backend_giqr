import os
import shutil
import subprocess
import sys
import threading

from dotenv import load_dotenv
from sqlalchemy_utils import database_exists, create_database

from app.sso_helper import domain_claims, syncronize_resource
from app.task.bridge import internalApi_byUrl

dotenv_path = os.path.join(os.path.dirname(__file__), ".env")
if os.path.exists(dotenv_path):
    load_dotenv(dotenv_path)

from sqlalchemy import MetaData, text
from flask_migrate import Migrate
from app import create_app, db

app = create_app(os.getenv("FLASK_CONFIG") or "default")
migrate = Migrate(app, db)


@app.shell_context_processor
def make_shell_context():
    # from app.api.DD_BIDKEG.model import DD_BIDKEG
    return dict(db=db,
                # DD_TAHAPAN=DD_TAHAPAN,
                )


@app.cli.command("clear_and_seed")
def clear_and_seed():
    msg = "\n ========== MIGRATION RESULT ==========\n"
    try:
        app.config["SQLALCHEMY_BINDS"] = {
            'default': os.getenv("DATABASE_URL")
        }
        connection_name = 'default'
        engine = db.get_engine(app, connection_name)
        print(engine)
        print(f'test connection to {connection_name} begin...')
        try:
            database_exists(engine.url)
        except Exception as e:
            print('database not found!')
            create_database(engine.url)
            print(f'create database {engine.url} begin...')

        if engine.execute(text('select 1')):
            msg = msg + f"- connection to {connection_name} success \n"

            # delete migrations folder
            print(f'delete migrations folder begin...')
            if os.path.isdir(os.path.join(sys.path[0] + "\\migrations")):
                shutil.rmtree(os.path.join(sys.path[0] + "\\migrations"))
                msg = msg + '- delete migrations folder success \n'

            try:
                print(f'drop table alembic_version begin...')
                engine.execute("drop table alembic_version")
                msg = msg + '- drop table alembic_version success \n'
            except Exception as e:
                msg = msg + '- drop alembic_version table passed \n'

            try:
                print(f'drop all app table begin...')
                meta = MetaData()
                meta.reflect(bind=db.get_engine(app, connection_name))
                meta.drop_all(bind=db.get_engine(app, connection_name))
                msg = msg + '- drop all app table success \n'
            except Exception as e:
                msg = msg + '- drop all app table passed \n'
                raise e

            try:
                print(f'prepare migration data and model begin...')
                subprocess.call("flask db init", shell=True)
                msg = msg + '- flask db init success \n'
                subprocess.call("flask db migrate", shell=True)
                msg = msg + '- flask db migrate success \n'
                subprocess.call("flask db upgrade", shell=True)
                msg = msg + '- flask db upgrade success \n'
            except Exception as e:
                raise e

            try:
                print(f'drop table alembic_version begin...')
                engine.execute("drop table alembic_version")
                msg = msg + '- drop table alembic_version success \n'
            except Exception as e:
                # print(e)
                msg = msg + '- drop alembic_version table passed \n'
        else:
            msg = msg + f"- connection to {connection_name} failed!\n"
        print(msg)
    except Exception as e:
        print(msg)
        raise e


@app.teardown_appcontext
def shutdown_session(exception=None):
    db.session.remove()


@app.teardown_request
def teardown_request(exception):
    if exception:
        db.session.rollback()
    db.session.remove()


@app.route('/internal/sync_resource', methods=['POST'])
def sync_resource():
    return syncronize_resource()


# @app.before_first_request
# def before_first_request():
#     syncronize_resource()

if __name__ == '__main__':
    # before_run_app()
    app.run(
        # host = "192.168.1.7",
        # port = 5000,
        # use_reloader=False
    threaded=True)