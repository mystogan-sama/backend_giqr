from flask_restx import fields

from app.utils import NullableString, NullableInteger

moduleTitle = ''
crudTitle = 'WEB_SERT'
apiPath = 'WEB_SERT'
modelName = 'WEB_SERT'
respAndPayloadFields = {
    "id": NullableInteger(readonly=True, example=1, ),
    "IDBRG": fields.String(required=True, max_length=10, example="", ),
    'id_unit': fields.Integer(required=False, description='Unit ID'),
    "NOFIKAT": fields.String(required=False, max_length=50, ),
    "ASETKEY": fields.String(required=False, max_length=50, example="", ),
    "NMASET": fields.String(required=False, max_length=150, example="", ),
    "UNITKEY": fields.String(required=False, max_length=50, example="", ),
    "TAHUN": fields.String(required=False, max_length=50, ),
    "DESA": fields.String(required=False, max_length=50, ),
    "BLOK": fields.String(required=False, max_length=50, ),
    "ALAMAT": fields.String(required=False, max_length=4000, ),
    "KORDINAT": fields.String(required=False, max_length=4000, ),
    "URLIMG": fields.String(required=True, max_length=1024, example="", ),
    'LUAS': fields.Float(required=False, description='Harga dalam USD'),
    "KET": fields.String(required=False, max_length=4000, ),
    "DATECREATE": fields.DateTime(required=False, example="2023-12-05 09:39", ),

}
uniqueField = []
searchField = ["NMASET","NMUNIT"]
sortField = []
filterField = ["UNITKEY", "NMASET","NMUNIT","ASETKEY", "id_unit"]
enabledPagination = True
fileFields = []

######################### GEN
moduleName = moduleTitle.replace(' ', '_').lower() + '_' if moduleTitle and len(moduleTitle) > 0 else ''
crudName = crudTitle.replace(' ', '_').lower() if crudTitle else ''
apiName = f'{moduleTitle} - {crudTitle}'
docName = f'{moduleName}{crudName}'