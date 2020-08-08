#!/usr/bin/python3

from db_admins import AdminDatabase
from db_computations import ComputationsDbSession
from db_computations import db_load_sheets
from db_computations import sheet_records
from db_personal import FittingSession
from db_personal import save_user_props
from flask import Flask
from flask import jsonify
from flask import make_response
from flask import redirect
from flask import render_template
from flask import request
from flask import send_from_directory
from shutil import copyfile

import os
import random

app = Flask(__name__)
app.config["UPLOAD_FOLDER"] = os.path.join(app.root_path, "files")
app.config["ALLOWED_EXTENSIONS"] = {".xlsx", ".xls", ".jpg", ".jpeg", ".png"}


@app.route("/admin-signin")
def admin_signin():
    return send_from_directory("static", "login.html")


@app.route("/admin-signin-submission", methods=["POST"])
def admin_signin_submission():
    username = request.form["username"]
    pwd = request.form["password"]
    adb = AdminDatabase()
    token = adb.get_token(username, pwd)
    adb.exit()
    resp = make_response(redirect("/p" if token != "notoken" else "/admin-signin"))
    resp.set_cookie('adminun', username)
    resp.set_cookie('admintkn', token)
    return resp


@app.route("/sheets")
def list_sheets():
    adb = AdminDatabase()
    istrue = adb.check_token(request.cookies.get('adminun'), request.cookies.get('admintkn'))
    adb.exit()
    if not istrue:
        return redirect("/admin-signin")
    path = os.path.abspath(".")
    files = os.listdir(os.path.join(path, "sheets", "brands"))
    files = ["CATALOGUE.XLSX"] + [f for f in files if "CATALOGUE" not in f]
    return render_template("files.html", files=files)


@app.route("/load_sheet", methods=["GET", "POST"])
@app.route("/sheet_acquire/<tname>")
def load_sheet(tname=None):
    if tname is None and "sheet-code" in request.form:
        tname = request.form["sheet-code"] + ".xlsx"

    elif tname is None:
        return redirect("/sheets")

    if ":" not in tname:
        num = random.randrange(111111, 999999)
        copyname = "%s:%d.XLSX" % (tname, num)
        try:
            copyfile(os.path.join("sheets", "brands", tname), os.path.join("copied", copyname))
        except FileNotFoundError:
            return redirect("/error/%s/%s" % ("No file holding the given number found", "sheets"))
        return redirect("/sheet_acquire/" + copyname)

    else:
        return send_from_directory("copied", tname)


'''
@app.route("/upload-file", methods=["GET", "POST"])
def upload_file():
    adb = AdminDatabase()
    istrue = adb.check_token(request.cookies.get('adminun'), request.cookies.get('admintkn'))
    adb.exit()
    if not istrue:
        return redirect("/admin-signin")
    if request.method == "POST":
        if "file" not in request.files:
            return redirect("/p")
        file = request.files['file']
        if file.filename == "":
            return redirect("/p")
        if file:
            file.save(os.path.join(app.root_path, "files", "LAST_UPLOADED.XLSX"))
            table.update_metatable("files/LAST_UPLOADED.XLSX")
            return redirect("/p?success=1")


@app.route("/upload-bm-file", methods=["GET", "POST"])
def upload_bm_files():
    if request.method == "POST":
        if "file" not in request.files:
            return jsonify({
                "error": "no_file_specified"
            })

        if "brand" not in request.form or "model" not in request.form:
            return jsonify({
                "error": "no_brand_model_data"
            })
        else:
            brand, model = request.form["brand"], request.form["model"]

        if "size" in request.form:
            size = request.form["size"]
        else:
            size = None

        if "userid" in request.form:
            user = request.form["user"]
        else:
            user = None

        file = request.files["file"]
        if file.filename == "":
            return jsonify({
                "error": "filename_not_found"
            })

        if file:
            extension = file.filename.split(".")[-1]
            fname = photos.new_photo_id(brand, model, extension)
            file.save(os.path.join(app.root_path, "files", fname))
            photos.add_photo(brand, model, size, fname, user)
            return jsonify({
                "new_photo_id": fname
            })
'''


@app.route("/p")
def panel():
    adb = AdminDatabase()
    istrue = adb.check_token(request.cookies.get('adminun'), request.cookies.get('admintkn'))
    adb.exit()
    if not istrue:
        return make_response(redirect("/admin-signin"))
    return send_from_directory("static", "tables.html")


@app.route("/_app_systems_of_size")
def _app_systems_of_size():
    return jsonify(
        ComputationsDbSession().systems_of_size(
            request.args["brand"], int(request.args["gender_int"]), request.args["standard"], request.args["size"]
        )
    )


@app.route("/_app_range_of_system")
def _app_range_of_system():
    return jsonify(
        ComputationsDbSession().range_of_system(
            request.args["brand"], int(request.args["gender_int"]), request.args["system"]
        )
    )


@app.route("/_app_recommended_size")
def _app_recommended_size():
    brand = request.args["brand"]
    gender_int = request.args["gender_int"]
    user_id = request.args["user_id"]
    s = ComputationsDbSession()
    # FIX IT !!!
    _recommended = ["UK", "4.5"]
    return jsonify(
        s.systems_of_size(brand, gender_int, *_recommended)
    )


@app.route("/error/<text>/<path:returnto>")
def throw_error(text, returnto):
    return render_template("error.html", text=text, returnto=returnto)


@app.route('/st/<path:path>')
def send_js(path):
    return send_from_directory('static', path)


if __name__ == "__main__":
    app.run(host="0.0.0.0")