from flask import render_template, current_app as app, request, jsonify
from flask_login import current_user
from . import blueprint, app_logger
from app.config import Config
from app.decorators import admin_required, enabled_required
from app import db
from datetime import datetime


# for Debuging
from icecream import ic

# App spezifische imports
from . import socketio_events
from . import api

from .helper_app_functions import helper_basic_app


# from .models import xx
# from app.admin.models import User@
# from app.helper_functions.helper_db_file import check_if_user_has_admin_rights

config = Config()
app_logger.info("Starte Routing für APP-EINKAUFSLISTE")
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
    all_my_chats = helper_basic_app.get_all_my_chats(current_user)
    get_current_time = helper_basic_app.get_current_time()
    return render_template(
        "BasicChat.html",
        user=current_user,
        config=config,
        app_config=app_config,
        all_my_chats=all_my_chats,
        get_current_time=get_current_time,
    )


app_logger.info("Ende Routing für APP-BASICCHAT")
