import decimal
import json
import math
from cgitb import text
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
        parser.add_argument('getLokasi', type=str, required=True, help='Your help message for getDaftAset')
        parser.add_argument('KDKIB', type=str)
        parser.add_argument('UNITKEY', type=str)
        parser.add_argument('ASETKEY', type=str)
        parser.add_argument('TAHUN', type=str)
        args = parser.parse_args()
        # print(args['page'])
        #
        if args['getLokasi'] == '1' and args['KDKIB'] and args['UNITKEY']:
            sql_query = """EXEC GET_ASET_FORGIS @KDKIB = :kdkib, @UNITKEY=:unitkey"""
            # Menambahkan ASETKEY ke query jika tersedia
            if args['ASETKEY']:
                sql_query += """, @ASETKEY=:asetkey"""

            # Menambahkan TAHUN ke query jika tersedia
            if args['TAHUN']:
                sql_query += """, @TAHUN=:tahun"""

            # Menjalankan query dengan parameter yang sesuai
            result = db.session.execute(sql_query,
                                        {'kdkib': args['KDKIB'], 'unitkey': args['UNITKEY'], 'asetkey': args['ASETKEY'],
                                         'tahun': args['TAHUN']})
            rows = result.fetchall()

            data = [dict(row) for row in rows]

            for item in data:
                for key, value in item.items():
                    if isinstance(value, datetime):
                        item[key] = value.isoformat()
                    elif isinstance(value, decimal.Decimal):
                        item[key] = float(value)

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

        else:
            return {'message': 'Invalid parameters'}, 400

        #
        #        resultFinal = []
        #        defaultPageResp = {
        #            "message": f'Get data {modelName} successfully',
        #            "status": True,
        #            "page": args['page'] or 1,
        #            "pages": args['page'] or 1,
        #            "per_page": args['length'] or 10,
        #            "total": 0,
        #            "data": resultFinal
        #        }
        #
        #        try:
        #            KDKIB = f"'{args.get('KDKIB')}'"
        #            UNITKEY = f"'{args.get('UNITKEY')}'"
        #            ASETKEY = f"'{args.get('ASETKEY')}'" if args.get('ASETKEY') else Null()
        #            TAHUN = f"'{args.get('TAHUN')}'" if args.get('TAHUN') else Null()
        #            page = f"{args['page'] if args.get('page') else 1}"
        #            length = f"{args['length'] if args.get('length') else 10}"
        #            sort = f"'{args.get('sort')}'" if args.get('sort') else Null()
        #            sort_dir = f"'{args.get('sort_dir')}'" if args.get('sort_dir') else Null()
        #            sqlQuery = f"EXEC GET_ASET_FORGIS @page={page}," \
        #                       f"@length={length},@sort={sort}," \
        #                       f"@sort_dir={sort_dir}," \
        #                       f"@search='{args['search'] or ''}'" \
        #                       f",@UNITKEY={UNITKEY}" \
        #                       f",@ASETKEY={ASETKEY}" \
        # \
        #                # print(sqlQuery)
        #            select_query = db.engine.execute(sqlQuery)
        #            results = [dict(row) for row in select_query]
        #            resultStr = json.dumps(results, cls=DateTimeEncoder)
        #            result = json.loads(resultStr)
        #
        #            if len(result) > 0:
        #                defaultPageResp['total'] = result[0]['total']
        #                defaultPageResp['pages'] = math.floor((result[0]['total'] or 0) / (args['length'] or 1))
        #                for row in result:
        #                    tgfikat_raw = row['TGFIKAT'].rstrip() if row['TGFIKAT'] else None
        #                    tgperolehan_raw = row['TGLPEROLEHAN'].rstrip() if row['TGLPEROLEHAN'] else None
        #
        #                    # mengecek jika TGFIKAT_raw mempunyai komponen wwaktu
        #                    tgfikat_date = datetime.strptime(tgfikat_raw, '%Y-%m-%d %H:%M').strftime(
        #                        '%Y-%m-%d') if tgfikat_raw and ' ' in tgfikat_raw else tgfikat_raw
        #                    tgperolehan_date = datetime.strptime(tgperolehan_raw, '%Y-%m-%d %H:%M').strftime(
        #                        '%Y-%m-%d') if tgperolehan_raw and ' ' in tgperolehan_raw else tgperolehan_raw
        #
        #                    # Mendapatkan nilai dari baris (row)
        #                    TAHUN = row['TAHUN']
        #                    NMHAK = row['NMHAK']
        #                    LUASTNH = row['LUASTNH']
        #                    NOFIKAT = row['NOFIKAT']
        #                    tgfikat_date = tgfikat_date
        #                    tgperolehan_date = tgperolehan_date
        #
        #                    NMHAK_str = NMHAK if NMHAK is not None else '-'
        #                    LUASTNH_str = LUASTNH if LUASTNH is not None else '-'
        #                    TAHUN_str = TAHUN if TAHUN is not None else '-'
        #                    NOFIKAT_str = NOFIKAT if NOFIKAT is not None else '-'
        #                    tgfikat_date_str = tgfikat_date if tgfikat_date is not None else '-'
        #                    tanggal_perolehan_str = tgperolehan_date if tgperolehan_date is not None else '-'
        #
        #                    resultFinal.append({
        #                        'id': row['id'],
        #                        'IDBRG': row['IDBRG'].rstrip() if row['IDBRG'] else None,
        #                        'UNITKEY': row['UNITKEY'].rstrip() if row['UNITKEY'] else None,
        #                        'ASETKEY': row['ASETKEY'].rstrip() if row['ASETKEY'] else None,
        #                        'KDUNIT': row['KDUNIT'].rstrip() if row['KDUNIT'] else None,
        #                        'NMUNIT': row['NMUNIT'].rstrip() if row['NMUNIT'] else None,
        #                        'KDASET': row['KDASET'].rstrip() if row['KDASET'] else None,
        #                        'NMASET': row['NMASET'].rstrip() if row['NMASET'] else None,
        #                        'NOREG': row['NOREG'].rstrip() if row['NOREG'] else None,
        #                        'KDLOKPO': row['KDLOKPO'].rstrip() if row['KDLOKPO'] else None,
        #                        'NIBAR': row['NIBAR'].rstrip() if row['NIBAR'] else None,
        #                        'ALAMAT': row['ALAMAT'].rstrip() if row['ALAMAT'] else None,
        #                        'NMSATUAN': row['NMSATUAN'].rstrip() if row['NMSATUAN'] else None,
        #                        'NILAI': str(row['NILAI']).rstrip() if row['NILAI'] is not None else None,
        #                        'NMKON': row['NMKON'].rstrip() if row['NMKON'] else None,
        #                        'PENGGUNA': row['PENGGUNA'].rstrip() if row['PENGGUNA'] else None,
        #                        'KET': row['KET'].rstrip() if row['KET'] else None,
        #                        'NMHAK': row['NMHAK'].rstrip() if row['NMHAK'] else None,
        #                        'LUASTNH': row['LUASTNH'] if row['LUASTNH'] else None,
        #                        'NOFIKAT': row['NOFIKAT'].rstrip() if row['NOFIKAT'] else None,
        #                        'TGFIKAT': tgfikat_date_str,
        #                        'TGLPEROLEHAN': tanggal_perolehan_str,
        #                        'TAHUN': row['TAHUN'].rstrip() if row['TAHUN'] else None,
        #                        'KOORDINAT': row['KOORDINAT'].rstrip() if row['KOORDINAT'] else None,
        #                        'detail_id': row['detail_id'] if row['detail_id'] else None,
        #                        'detail_status': row['detail_status'] if row['detail_status'] else None,
        #                        'ATR_INDUKSPEKNAMA': f"Tahun: {TAHUN_str}, Luas: {LUASTNH_str}M², Nama Sertifikat: {NMHAK_str}, No Sertifikat: {NOFIKAT_str}, Tanggal Sertifikat: {tgfikat_date_str},Tanggal Perolehan: {tanggal_perolehan_str}",
        #                        'GANDA_SPEKNAMA': f"Tahun: {TAHUN_str}, Luas: {LUASTNH_str}M², Nama Sertifikat: {NMHAK_str}, No Sertifikat: {NOFIKAT_str}, Tanggal Sertifikat: {tgfikat_date_str},Tanggal Perolehan: {tanggal_perolehan_str}",
        #
        #                    })
        #                    # print(resultFinal)
        #            return defaultPageResp, 200
        #        except Exception as e:
        #            defaultPageResp['message'] = f'Get data {modelName} failed!'
        #            defaultPageResp['status'] = False
        #            logger.error(e)
        #            return defaultPageResp, 500

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
                f"FROM GIS_ASET AS l "
                f"LEFT JOIN PEGAWAI AS p ON l.UNITKEY = p.UNITKEY "
                f"WHERE p.UNITKEY = (SELECT TOP 1 l.UNITKEY FROM GIS_ASET l WHERE l.id = {id}) AND p.KDPOSTTD = '1';"
                f"SELECT @PENGELOLABRG = REPLACE(p.CONFIGVAL, 'PEMERINTAH DAERAH ', '') "
                f"FROM PEMDA p "
                f"WHERE p.CONFIGID = 'pemda_w';"
                f"SELECT @KOTA = p.CONFIGVAL "
                f"FROM PEMDA p "
                f"WHERE p.CONFIGID = 'pemda_i';"
                f"SELECT @UNITKEY = l.UNITKEY "
                f"FROM GIS_ASET l "
                f"WHERE l.id = {id};"
                f"SELECT s.*, s.id AS detail_id, "
                f"@KSBRG AS PENGGUNABRG, @PENGELOLABRG AS PENGELOLABRG, @KSBRG AS KUASABRG, @KOTA AS LOKASIPEMDA, "
                f"l.ID as id_GIS_ASET, l.[IDBRG], l.[UNITKEY], l.[ASETKEY], l.[KDUNIT], l.[NMUNIT], "
                f"l.[KDASET], l.[NMASET], l.[NOREG], l.[NILAI], l.[NMSATUAN], l.[NMKON], l.[PENGGUNA], l.[ALAMAT], "
                f"l.[KET], l.[KDLOKPO], l.[NIBAR], l.[TGLPEROLEHAN], l.[KOORDINAT],"
                f"l.[NMHAK],l.[TAHUN], l.[LUASTNH], l.[NOFIKAT], l.[TGFIKAT] "
                f"FROM GIS_ASET l LEFT OUTER JOIN SensusTanah s "
                f"ON l.ID = s.id_GIS_ASET "
                f"WHERE l.ID = {id}"
            )

            # print(sqlQuery)
            select_query = db.engine.execute(sqlQuery)
            results = [dict(row) for row in select_query]
            resultStr = json.dumps(results, cls=DateTimeEncoder)
            result = json.loads(resultStr)
            if result:
                resultFinal = result[0]
                resultFinal['id'] = result[0]['id_GIS_ASET']
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

    #### PUT
    @doc.putRespDoc
    @api.expect(doc.default_data_response)
    @token_required
    def put(self, id):
        request_put = request.get_json()
        print(request_put)

        # Dapatkan data berdasarkan ID_LOK
        #data_to_update = WEB_KIBLOKASI.query.filter_by(ID_LOK=id).first()
        #
        # if data_to_update:
        #     # Update data berdasarkan request_put
        #     data_to_update.IDBRG = request_put.get('IDBRG')
        #     data_to_update.TAHUN = request_put.get('TAHUN')
        #     data_to_update.ASETKEY = request_put.get('ASETKEY')
        #     data_to_update.KET = request_put.get('KET')
        #     data_to_update.UNITKEY = request_put.get('UNITKEY')
        #     data_to_update.KDKIB = request_put.get('KDKIB')
        #     data_to_update.URLIMG = request_put.get('URLIMG')
        #     data_to_update.URLIMG1 = request_put.get('URLIMG1')
        #     data_to_update.URLIMG2 = request_put.get('URLIMG2')
        #     data_to_update.URLIMG3 = request_put.get('URLIMG3')
        #
        #     # Simpan perubahan ke database
        #     db.session.commit()
        #
        #     return jsonify({
        #         "message": "Data berhasil diupdate",
        #         "status": True,
        #         "data": request_put  # Anda dapat mengembalikan data yang diupdate jika perlu
        #     }), 200
        # else:
        #     # Jika data tidak ditemukan berdasarkan ID_LOK
        #     return jsonify({
        #         "message": "Data dengan ID_LOK tersebut tidak ditemukan",
        #         "status": False,
        #         "data": {}
        #     }), 404

        # print(insert_data)
    #### DELETE
    @doc.deleteRespDoc
    @token_required
    def delete(self, id):
        return GeneralDeleteById(id, doc, crudTitle, Service, request, modelName, current_user, fileFields,
                                 internalApi_byUrl)

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