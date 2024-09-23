from datetime import datetime
from threading import Thread

from sqlalchemy import event

from app import db
from app.sso_helper import check_unit_privilege_on_changes_db, insert_user_activity, current_user, \
    check_unit_and_employee_privilege_on_read_db
from app.utils import row2dict
from . import crudTitle, apiPath, modelName


class WEB_KIBLOKASI(db.Model):
    __tablename__ = 'WEB_KIBLOKASI'
    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    IDBRG = db.Column(db.String(10), nullable=False)
    UNITKEY = db.Column(db.String(36), nullable=True)
    NMUNIT = db.Column(db.String(1024), nullable=True)
    ASETKEY = db.Column(db.String(15), nullable=True)
    KDASET = db.Column(db.String(1024), nullable=True)
    TAHUN = db.Column(db.String(5), nullable=True)
    KET = db.Column(db.String(4000), nullable=True)
    METODE = db.Column(db.String(40), nullable=True)
    LOKASI = db.Column(db.String(4000), nullable=True)
    DATECREATE = db.Column(db.DateTime, default=datetime.now, nullable=True)
    KDKIB = db.Column(db.String(2), nullable=True)
    URLIMG = db.Column(db.String(1024), nullable=True)
    URLIMG1 = db.Column(db.String(1024), nullable=True)
    URLIMG2 = db.Column(db.String(1024), nullable=True)
    URLIMG3 = db.Column(db.String(1024), nullable=True)
    ID_ASET = db.Column(db.BigInteger)
    NOFIKAT = db.Column(db.String(50), nullable=True)

# BEFORE TRANSACTION: CHECK PRIVILEGE UNIT
@event.listens_for(db.session, "do_orm_execute")
def check_unit_privilege_read(orm_execute_state):
    check_unit_and_employee_privilege_on_read_db(orm_execute_state, WEB_KIBLOKASI)