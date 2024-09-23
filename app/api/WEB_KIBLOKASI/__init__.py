from flask_restx import fields

from app.utils import NullableString, NullableInteger

moduleTitle = ''
crudTitle = 'WEB_KIBLOKASI'
apiPath = 'WEB_KIBLOKASI'
modelName = 'WEB_KIBLOKASI'
respAndPayloadFields = {
    "id": NullableInteger(readonly=True, example=1, ),
    "IDBRG": fields.String(required=True, max_length=10, example="", ),
    "UNITKEY": fields.String(required=False, max_length=36, example="", ),
    "NMUNIT": fields.String(required=False, max_length=36, example="", ),
    "ASETKEY": fields.String(required=False, max_length=15, example="", ),
    "KDASET": fields.String(required=False, max_length=15, example="", ),
    "TAHUN": fields.String(required=False, max_length=5, ),
    "KET": fields.String(required=False, max_length=4000, ),
    "METODE": fields.String(required=False, max_length=40, ),
    "LOKASI": fields.String(required=False, max_length=4000, ),
    "DATECREATE": fields.DateTime(required=False, example="2023-12-05 09:39", ),
    "KDKIB": fields.String(required=False, max_length=2, example="", ),
    "URLIMG": fields.String(required=True, max_length=1024, example="", ),
    "URLIMG1": fields.String(required=True, max_length=1024, example="", ),
    "URLIMG2": fields.String(required=True, max_length=1024, example="", ),
    "URLIMG3": fields.String(required=True, max_length=1024, example="", ),
    "ID_ASET": NullableInteger(),
    "NOFIKAT": fields.String(required=False, max_length=40, ),

}
uniqueField = []
searchField = ["NMASET","NMUNIT"]
sortField = []
filterField = ["UNITKEY", "NMASET","NMUNIT","ASETKEY", "getWEB_KIBLOKASI"]
enabledPagination = True
fileFields = []

######################### GEN
moduleName = moduleTitle.replace(' ', '_').lower() + '_' if moduleTitle and len(moduleTitle) > 0 else ''
crudName = crudTitle.replace(' ', '_').lower() if crudTitle else ''
apiName = f'{moduleTitle} - {crudTitle}'
docName = f'{moduleName}{crudName}'