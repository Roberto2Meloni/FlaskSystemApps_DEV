from flask import render_template, current_app as app, request, jsonify
from flask_login import current_user
from . import blueprint
from app.config import Config
from app.decorators import admin_required, enabled_required
from app import db

# for Debuging
from icecream import ic

# from .models import xx
# from app.admin.models import User@
# from app.helper_functions.helper_db_file import check_if_user_has_admin_rights

config = Config()

print("Template_app_v000 Version 0.0.0")


@blueprint.route("/Template_app_v000_index", methods=["GET"])
@enabled_required
def Template_app_v000_index():
    return render_template(
        "Template_app_v000_index.html", user=current_user, config=config
    )
