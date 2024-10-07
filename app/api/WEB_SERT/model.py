from datetime import datetime
from threading import Thread

from sqlalchemy import event

from app import db
from app.sso_helper import check_unit_privilege_on_changes_db, insert_user_activity, current_user, \
    check_unit_and_employee_privilege_on_read_db
from app.utils import row2dict
from . import crudTitle, apiPath, modelName


class WEB_SERT(db.Model):
    __tablename__ = 'WEB_SERT'
    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    IDBRG = db.Column(db.String(10), nullable=False)
    id_unit = db.Column(db.BigInteger, nullable=True)
    NOFIKAT = db.Column(db.String(50), nullable=True)
    ASETKEY = db.Column(db.String(50), nullable=True)
    NMASET = db.Column(db.String(150), nullable=True)
    UNITKEY = db.Column(db.String(50), nullable=True)
    TAHUN = db.Column(db.String(50), nullable=True)
    DESA = db.Column(db.String(50), nullable=False)
    BLOK = db.Column(db.String(50), nullable=False)
    ALAMAT = db.Column(db.String(4000), nullable=True)
    KORDINAT = db.Column(db.String(4000), nullable=True)
    URLIMG = db.Column(db.String(1024), nullable=True)
    LUAS = db.Column(db.DECIMAL(18, 1), default=0, nullable=True)
    KET = db.Column(db.String(4000), nullable=True)
    DATECREATE = db.Column(db.DateTime, default=datetime.now, nullable=True)

# BEFORE TRANSACTION: CHECK PRIVILEGE UNIT
@event.listens_for(db.session, "do_orm_execute")
def check_unit_privilege_read(orm_execute_state):
    check_unit_and_employee_privilege_on_read_db(orm_execute_state, WEB_SERT)