from flask import render_template, current_app as app, request, jsonify
from flask_login import current_user
from . import blueprint
from app.config import Config
from app.decorators import admin_required, enabled_required
from app import db
from datetime import datetime


from .helper_app_functions import helper_basic_app


@blueprint.route("/get_chat_contanten/<chat_room_number>", methods=["GET"])
@enabled_required
def get_chat_contanten(chat_room_number):
    """
    Holt Chat-Informationen anhand der room_number
    """
    try:
        chat, chat_type, error_message = helper_basic_app.find_chat_by_room_number(
            chat_room_number, current_user
        )

        if chat is None:
            return jsonify(
                {"success": False, "error": error_message, "chat": None, "type": None}
            ), (403 if error_message == "Keine Berechtigung" else 404)

        return jsonify(
            {
                "success": True,
                "chat": chat,
                "type": chat_type,
                "error_message": error_message,
            }
        )

    except Exception as e:
        print(f"❌ Fehler in get_chat_contanten: {e}")
        return (
            jsonify(
                {"success": False, "error": "Serverfehler", "chat": None, "type": None}
            ),
            500,
        )


@blueprint.route("/get_chat_messages/<chat_room_number>", methods=["GET"])
@enabled_required
def get_chat_messages(chat_room_number):
    """
    Placeholder für Chat-Nachrichten (kommt in Phase 2)
    """
    try:
        # Prüfe erst ob User Zugriff auf diesen Chat hat
        chat, chat_type, error_message = helper_basic_app.find_chat_by_room_number(
            chat_room_number, current_user
        )

        if chat is None:
            return jsonify(
                {"success": False, "error": error_message, "messages": []}
            ), (403 if error_message == "Keine Berechtigung" else 404)

        # Placeholder - keine echten Nachrichten yet
        return jsonify(
            {
                "success": True,
                "messages": [],
                "count": 0,
                "room_number": chat_room_number,
                "chat_type": chat_type,
                "info": "Nachrichten-Funktionalität kommt in Phase 2",
            }
        )

    except Exception as e:
        print(f"❌ Fehler in get_chat_messages: {e}")
        return jsonify({"success": False, "error": "Serverfehler", "messages": []}), 500


@blueprint.route("/api/chat_rooms", methods=["GET"])
@enabled_required
def api_chat_rooms():
    """
    API Endpoint für alle User-Chats (für AJAX-Calls)
    """
    try:
        all_my_chats = get_all_my_chats(current_user)

        chats_data = []
        for chat in all_my_chats:
            if hasattr(chat, "group_name"):  # Group Chat
                chats_data.append(
                    {
                        "room_number": chat.chat_room_number,
                        "name": chat.group_name,
                        "type": "group",
                        "last_message": chat.last_message,
                        "last_message_date": (
                            chat.last_message_date.isoformat()
                            if chat.last_message_date
                            else None
                        ),
                    }
                )
            else:  # Normal Chat
                chats_data.append(
                    {
                        "room_number": chat.chat_room_number,
                        "name": f"Chat {chat.a_user_id}-{chat.b_user_id}",  # Placeholder
                        "type": "normal",
                        "last_message": chat.last_message,
                        "last_message_date": (
                            chat.last_message_date.isoformat()
                            if chat.last_message_date
                            else None
                        ),
                    }
                )

        return jsonify({"success": True, "chats": chats_data, "count": len(chats_data)})

    except Exception as e:
        print(f"❌ Fehler in api_chat_rooms: {e}")
        return jsonify({"success": False, "error": "Serverfehler", "chats": []}), 500


@blueprint.route("/api/room_status/<chat_room_number>", methods=["GET"])
@enabled_required
def api_room_status(chat_room_number):
    """
    Gibt Status-Informationen über einen Chat-Raum zurück
    """
    try:
        chat, chat_type, error_message = helper_basic_app.find_chat_by_room_number(
            chat_room_number, current_user
        )

        if chat is None:
            return jsonify(
                {"success": False, "error": error_message, "has_access": False}
            ), (403 if error_message == "Keine Berechtigung" else 404)

        return jsonify(
            {
                "success": True,
                "has_access": True,
                "room_number": chat_room_number,
                "chat_type": chat_type,
                "room_exists": True,
            }
        )

    except Exception as e:
        print(f"❌ Fehler in api_room_status: {e}")
        return (
            jsonify({"success": False, "error": "Serverfehler", "has_access": False}),
            500,
        )
