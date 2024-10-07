from flask_restx import fields

from app.utils import NullableString, NullableInteger

moduleTitle = ''
crudTitle = 'WEB_SEWA'
apiPath = 'WEB_SEWA'
modelName = 'WEB_SEWA'
respAndPayloadFields = {
    "id": NullableInteger(readonly=True, example=1, ),
    "IDBRG": fields.String(required=True, max_length=10, example="", ),
    "NOFIKAT": fields.String(required=False, max_length=50, ),
    "NAMA": fields.String(required=False, max_length=50, example="", ),
    "ALAMAT": fields.String(required=False, max_length=4000, ),
    'LUAS': fields.Float(required=False, description=''),
    "PERUNTUKAN": fields.String(required=False, max_length=4000, ),
    "STARTDATE": fields.DateTime(required=False, example="2023-12-05 09:39", ),
    "ENDDATE": fields.DateTime(required=False, example="2023-12-05 09:39", ),
    'BESARANSEWA': fields.Float(required=False, description=''),
    "URLIMGSEWA": fields.String(required=True, max_length=1024, example="", ),
    "METODE": fields.String(required=False, max_length=4000, ),
    "KORDINAT": fields.String(required=False, max_length=4000, ),
    "DESA": fields.String(required=False, max_length=50, ),
    "NOHAKPAKAI": fields.String(required=False, max_length=50, ),
    "TAHUNHAKPAKAI": fields.String(required=False, max_length=50, ),
    "NOSKBUP": fields.String(required=False, max_length=50, ),
    "NOMOU": fields.String(required=False, max_length=50, ),
    "KET": fields.String(required=False, max_length=4000, ),
    'STATUS': fields.Integer(required=False, description=''),
    "DATECREATE": fields.DateTime(required=False, example="2023-12-05 09:39", ),

}
uniqueField = []
searchField = ["NMASET","NMUNIT"]
sortField = []
filterField = ["UNITKEY", "NMASET","NMUNIT","ASETKEY", "IDBRG"]
enabledPagination = True
fileFields = []

######################### GEN
moduleName = moduleTitle.replace(' ', '_').lower() + '_' if moduleTitle and len(moduleTitle) > 0 else ''
crudName = crudTitle.replace(' ', '_').lower() if crudTitle else ''
apiName = f'{moduleTitle} - {crudTitle}'
docName = f'{moduleName}{crudName}'