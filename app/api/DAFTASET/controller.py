import decimal
import json
import math
from sqlalchemy.sql import text as sqlalchemy_text
from datetime import datetime


from flask import request, current_app, jsonify
from flask_restx import Resource, reqparse, inputs
from sqlalchemy import create_engine, exc
from sqlalchemy.orm import sessionmaker
from sqlalchemy.sql.elements import Null

from app.utils import GeneralGetList, \
    GeneralPost, GeneralDelete, GeneralGetById, GeneralPutById, GeneralDeleteById, generateDefaultResponse, message, \
    error_response, DateTimeEncoder, logger
from . import crudTitle, enabledPagination, respAndPayloadFields, fileFields, modelName, filterField
from .doc import doc
from .service import Service
from ... import internalApi_byUrl, db
from ...sso_helper import token_required, current_user

api = doc.api

parser = reqparse.RequestParser()
parser.add_argument('fetch_child', type=inputs.boolean, help='boolean input for fetch unit children', default=True)

parser.add_argument('sort', type=str, help='for sorting, fill with column name')
parser.add_argument('sort_dir', type=str, choices=('asc', 'desc'), help='fill with "asc" or "desc"')


#### LIST
@api.route("")
class List(Resource):
    if enabledPagination:
        parser.add_argument('page', type=int, help='page/start, fill with number')
        parser.add_argument('length', type=int, help='length of data, fill with number')
        parser.add_argument('search', type=str, help='for filter searching')
    if filterField:
        for row in filterField:
            parser.add_argument(
                f"{row.replace(':', '').replace('>', '').replace('<', '').replace('=', '').replace('!', '')}")

    #### GET
    @doc.getRespDoc
    @api.expect(parser)
    # @token_required
    def get(self):
        parser = reqparse.RequestParser()
        parser.add_argument('getDaftAset', type=str, required=True, help='Your help message for getDaftAset')
        parser.add_argument('KDKIB', type=str)
        parser.add_argument('UNITKEY', type=str)
        parser.add_argument('kd_jenis', type=str)
        parser.add_argument('id_unit', type=str)
        args = parser.parse_args()

        # Helper function to process query results
        def process_query_result(result):
            # Check if result is empty
            if result.rowcount == 0:
                return []  # Return an empty list if no rows are found

            # Otherwise, fetch the results
            rows = result.fetchall()

            # Convert rows to a list of dictionaries (JSON-like)
            data = [dict(row) for row in rows]

            # Convert datetime objects to string representation
            for item in data:
                for key, value in item.items():
                    if isinstance(value, datetime):
                        item[key] = value.isoformat()
                    elif isinstance(value, decimal.Decimal):
                        item[key] = float(value)

            return data

        # Handle 'getDaftAset' == '1'
        if args.get("getDaftAset") == '1' and args['KDKIB'] and args['UNITKEY']:
            sql_query = """EXEC GET_DAFTASET @KDKIB=:kdkib, @UNITKEY=:unitkey"""
            result = db.session.execute(sql_query, {'kdkib': args['KDKIB'], 'unitkey': args['UNITKEY']})
            data = process_query_result(result)

            response = {
                "status": True,
                "message": "data sent",
                "page": 1,
                "pages": 1,
                "per_page": 10,
                "total": len(data),
                "has_next": False,
                "next_num": None,
                "prev_num": None,
                "data": data
            }
            return response, 200

        elif args.get("getDaftAset") == '2' and args.get('kd_jenis') and args.get('id_unit'):
            id_unit = int(args.get("id_unit"))
            kd_jenis = str(args.get("kd_jenis"))

            # SQL Query dengan penamaan parameter yang sesuai
            sql_query = "EXEC lookup_asetForQr @id_unit=4010003223715, @kd_jenis='1.3.1'"

            try:
                # Menjalankan query dengan parameter yang benar
                # result = db.session.execute(sql_query, {"id_unit": id_unit, "kd_jenis": kd_jenis})
                result = db.session.execute(sql_query)
                print(result)
                rows = result.fetchall()
                print(rows)
                # Cek apakah hasil query kosong
                if not result.returns_rows:
                    return {'message': 'No rows returned from the stored procedure'}, 200

                # Proses data hasil query
                data = []
                for rowproxy in result:
                    row_dict = {}
                    for column, value in rowproxy.items():
                        if isinstance(value, datetime):
                            row_dict[column] = value.isoformat()
                        elif isinstance(value, decimal.Decimal):
                            row_dict[column] = float(value)
                        else:
                            row_dict[column] = value
                    data.append(row_dict)

                # Persiapkan response
                resp = message(True, generateDefaultResponse(crudTitle, 'get-list', 200))
                resp['data'] = data
                return resp, 200

            except Exception as e:
                # Tangani error
                return {'message': f"Error executing stored procedure: {str(e)}"}, 500

        # Invalid parameters
        return {'message': 'Invalid parameters'}, 400



#### BY ID
@api.route("/<int:id>")
class ById(Resource):
    #### GET
    @doc.getByIdRespDoc
    @token_required
    def get(self, id):
        resultFinal = {}
        try:
            sqlQuery = (
                f"DECLARE @PENGELOLABRG VARCHAR(100), @KOTA VARCHAR(50), @KSBRG VARCHAR(100), @UNITKEY VARCHAR(100);"
                f"SELECT  @KSBRG = p.JABATAN "
                f"FROM DAFTASET AS l "
                f"LEFT JOIN PEGAWAI AS p ON l.UNITKEY = p.UNITKEY "
                f"WHERE p.UNITKEY = (SELECT TOP 1 l.UNITKEY FROM DAFTASET l WHERE l.id = {id}) AND p.KDPOSTTD = '1';"
                f"SELECT @PENGELOLABRG = REPLACE(p.CONFIGVAL, 'PEMERINTAH DAERAH ', '') "
                f"FROM PEMDA p "
                f"WHERE p.CONFIGID = 'pemda_w';"
                f"SELECT @KOTA = p.CONFIGVAL "
                f"FROM PEMDA p "
                f"WHERE p.CONFIGID = 'pemda_i';"
                f"SELECT @UNITKEY = l.UNITKEY "
                f"FROM DAFTASET l "
                f"WHERE l.id = {id};"
                f"SELECT s.*, s.id AS detail_id, "
                f"@KSBRG AS PENGGUNABRG, @PENGELOLABRG AS PENGELOLABRG, @KSBRG AS KUASABRG, @KOTA AS LOKASIPEMDA, "
                f"l.ID as id_DAFTASET, l.[IDBRG], l.[UNITKEY], l.[ASETKEY], l.[KDUNIT], l.[NMUNIT], "
                f"l.[KDASET], l.[NMASET], l.[NOREG], l.[NILAI], l.[NMSATUAN], l.[NMKON], l.[PENGGUNA], l.[ALAMAT], "
                f"l.[KET], l.[KDLOKPO], l.[NIBAR], l.[TGLPEROLEHAN], l.[KOORDINAT],"
                f"l.[NMHAK],l.[TAHUN], l.[LUASTNH], l.[NOFIKAT], l.[TGFIKAT] "
                f"FROM DAFTASET l LEFT OUTER JOIN SensusTanah s "
                f"ON l.ID = s.id_DAFTASET "
                f"WHERE l.ID = {id}"
            )

            # print(sqlQuery)
            select_query = db.engine.execute(sqlQuery)
            results = [dict(row) for row in select_query]
            resultStr = json.dumps(results, cls=DateTimeEncoder)
            result = json.loads(resultStr)
            if result:
                resultFinal = result[0]
                resultFinal['id'] = result[0]['id_DAFTASET']
                # memasukan data yang di inginkan ke variabel untuk di masukan ke SPEK_NAMABAR

                luastnh = resultFinal.get('LUASTNH', '-') or ' - '
                tgfikat_raw = resultFinal.get('TGFIKAT', '- ') or ' - '

                # mengecek jika TGFIKAT_raw mempunyai komponen waktu
                tgfikat_date = datetime.strptime(tgfikat_raw, '%Y-%m-%d %H:%M').strftime(
                    '%Y-%m-%d') if ' ' in tgfikat_raw else tgfikat_raw
                tglperolehan_raw = resultFinal.get('TGLPEROLEHAN', '') or ' - '

                if resultFinal['TGLPEROLEHAN_SESUAI'] is not None:
                    tahunperolehan_raw = resultFinal['TGLPEROLEHAN_SESUAI']
                else:
                    tahunperolehan_raw = ''

                # Extract date part from TGLPEROLEHAN
                tglperolehan_date = datetime.strptime(tglperolehan_raw, '%Y-%m-%d %H:%M').strftime(
                    '%Y-%m-%d') if ' ' in tglperolehan_raw else tglperolehan_raw

                if tahunperolehan_raw and ' ' in tahunperolehan_raw:
                    tahun_perolehan = datetime.strptime(tahunperolehan_raw, '%Y-%m-%d %H:%M').strftime('%Y')
                else:
                    tahun_perolehan = tahunperolehan_raw

                resultFinal['TGLPEROLEHAN'] = f"{tglperolehan_date}"

                # Set TAHUN_SESUAI to the year from TGLPEROLEHAN
                resultFinal['TAHUN_SESUAI'] = f"{tahun_perolehan[:4]}"
                resultFinal['LUASTNH'] = f"{luastnh} M²"
                resultFinal['TGFIKAT'] = f"{tgfikat_date}"

            return {
                "message": "Success",
                "status": True,
                "data": resultFinal
            }, 200
        except Exception as e:
            logger.error(e)
            return {
                "message": "Error",
                "status": False,
                "data": resultFinal
            }, 500


        # return GeneralGetById(id, doc, crudTitle, Service)


#### GET SUMMARY
@api.route("/summary")
class Summary(Resource):
    @doc.getSummaryRespDoc
    @token_required
    def get(self):
        try:
            args = parser.parse_args()
            resultData = Service.getSummary(args)
            # if not resultData:
            #     return error_response(generateDefaultResponse(crudTitle, 'get-sum', 500), 500)
            resp = message(True, generateDefaultResponse(crudTitle, 'get-sum', 200))
            resp['data'] = resultData
            return resp, 200
        except Exception as e:
            current_app.logger.error(e)
            return error_response(generateDefaultResponse(crudTitle, 'get-sum', 500), 500)