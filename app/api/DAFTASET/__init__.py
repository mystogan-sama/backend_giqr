from flask_restx import fields

from app.utils import NullableString, NullableInteger

moduleTitle = ''
crudTitle = 'DAFTASET'
apiPath = 'DAFTASET'
modelName = 'DAFTASET'
respAndPayloadFields = {
    "id": NullableInteger(readonly=True, example=1, ),
    "IDBRG": fields.String(required=True, max_length=10, example="", ),
    "UNITKEY": fields.String(required=False, max_length=36, example="", ),
    "KDUNIT": fields.String(required=False, max_length=30, ),
    "NMUNIT": fields.String(required=False, max_length=500, ),
    "ASETKEY": fields.String(required=False, max_length=15, example="", ),
    "KDASET": fields.String(required=False, max_length=30, ),
    "NMASET": fields.String(required=False, max_length=254, ),
    "TAHUN": fields.String(required=False, max_length=5, ),
    "NOREG": fields.String(required=False, max_length=10, ),
    "NILAI": fields.String(required=False, max_length=30, ),
    "KDKIB": fields.String(required=False, max_length=2, example="", ),
    "KDSATUAN": fields.String(required=False, max_length=2, example="", ),
    "NMSATUAN": fields.String(required=False, max_length=20, ),
    "KDKON": fields.String(required=False, max_length=2, example="", ),
    "NMKON": fields.String(required=False, max_length=30, ),
    "PENGGUNA": fields.String(required=False, max_length=254, ),
    "KDHAK": fields.String(required=False, max_length=2, example="", ),
    "NMHAK": fields.String(required=False, max_length=20, ),
    "LUASTNH": fields.String(required=False, ),
    "NOFIKAT": fields.String(required=False, max_length=50, ),
    "TGFIKAT": fields.DateTime(required=False, example="2023-12-05 09:39", ),
    "ALAMAT": fields.String(required=False, max_length=512, ),
    "KET": fields.String(required=False, max_length=4000, ),
    "TGLPEROLEHAN": fields.DateTime(required=False, example="2023-12-05 09:39", ),
    "KDKLAS": fields.String(required=False, max_length=2, example="", ),
    "NMKLAS": fields.String(required=True, max_length=6, example="", ),
    "KDLOKPO": fields.String(required=False, max_length=133, ),
    "NIBAR": fields.String(required=False, max_length=13, ),
    "ASALUSUL": fields.String(required=False, max_length=512, ),
    "KOORDINAT": fields.String(required=False, max_length=512, ),

}
uniqueField = []
searchField = ["NMASET","NMUNIT"]
sortField = []
filterField = ["UNITKEY", "NMASET","NMUNIT","ASETKEY", "getDaftAset", "kd_jenis", "id_unit"]
enabledPagination = True
fileFields = []

######################### GEN
moduleName = moduleTitle.replace(' ', '_').lower() + '_' if moduleTitle and len(moduleTitle) > 0 else ''
crudName = crudTitle.replace(' ', '_').lower() if crudTitle else ''
apiName = f'{moduleTitle} - {crudTitle}'
docName = f'{moduleName}{crudName}'