from datetime import datetime
from threading import Thread

from sqlalchemy import event

from app import db
from app.sso_helper import check_unit_privilege_on_changes_db, insert_user_activity, current_user, \
    check_unit_and_employee_privilege_on_read_db
from app.utils import row2dict
from . import crudTitle, apiPath, modelName


class JNSKIB(db.Model):
    __tablename__ = 'JNSKIB'
    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    IDBRG = db.Column(db.String(10), nullable=False)
    UNITKEY = db.Column(db.String(36), nullable=True)
    KDUNIT = db.Column(db.String(30), nullable=True)
    NMUNIT = db.Column(db.String(500), nullable=True)
    ASETKEY = db.Column(db.String(15), nullable=True)
    KDASET = db.Column(db.String(30), nullable=True)
    NMASET = db.Column(db.String(254), nullable=True)
    TAHUN = db.Column(db.String(5), nullable=True)
    NOREG = db.Column(db.String(10), nullable=True)
    NILAI = db.Column(db.String(30), nullable=True)
    KDKIB = db.Column(db.String(2), nullable=True)
    KDSATUAN = db.Column(db.String(2), nullable=True)
    NMSATUAN = db.Column(db.String(20), nullable=True)
    KDKON = db.Column(db.String(2), nullable=True)
    NMKON = db.Column(db.String(30), nullable=True)
    PENGGUNA = db.Column(db.String(254), nullable=True)
    KDHAK = db.Column(db.String(2), nullable=True)
    NMHAK = db.Column(db.String(20), nullable=True)
    LUASTNH = db.Column(db.String(20), nullable=True)
    NOFIKAT = db.Column(db.String(50), nullable=True)
    TGFIKAT = db.Column(db.DateTime, default=datetime.now, nullable=True)
    ALAMAT = db.Column(db.String(512), nullable=True)
    KET = db.Column(db.String(4000), nullable=True)
    TGLPEROLEHAN = db.Column(db.DateTime, default=datetime.now, nullable=True)
    KDKLAS = db.Column(db.String(2), nullable=True)
    NMKLAS = db.Column(db.String(6), nullable=False)
    KDLOKPO = db.Column(db.String(133), nullable=True)
    NIBAR = db.Column(db.String(13), nullable=True)
    ASALUSUL = db.Column(db.String(512), nullable=True)
    KOORDINAT = db.Column(db.String(512), nullable=True)

# BEFORE TRANSACTION: CHECK PRIVILEGE UNIT
@event.listens_for(db.session, "do_orm_execute")
def check_unit_privilege_read(orm_execute_state):
    check_unit_and_employee_privilege_on_read_db(orm_execute_state, JNSKIB)