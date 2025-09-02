from flask import render_template, current_app as app, request, jsonify
from flask_login import current_user
from . import blueprint
from app.config import Config
from app.decorators import admin_required, enabled_required
from app import db
from datetime import datetime


# for Debuging
from icecream import ic

# App spezifische imports
from . import socketio_events

from .helper_app_functions import helper_basic_app


# from .models import xx
# from app.admin.models import User@
# from app.helper_functions.helper_db_file import check_if_user_has_admin_rights

config = Config()

print("BasicChat Version 0.0.0")


@blueprint.route("/BasicChat_index", methods=["GET"])
@enabled_required
def BasicChat_index():
    try:
        with app.app_context():
            helper_basic_app.create_global_group_chat()
            app.logger.debug("Datenbank erweiterung abgeschlossen?")
    except Exception as e:
        app.logger.error(f"Fehler beim Erweitern der Datenbank: {e}")
    app_config = helper_basic_app.get_app_config()
    return render_template(
        "BasicChat.html",
        user=current_user,
        config=config,
        app_config=app_config,
    )
