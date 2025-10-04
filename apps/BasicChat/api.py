from flask import render_template, current_app as app, request, jsonify
from flask_login import current_user
from . import blueprint, app_logger
from app.config import Config
from app.decorators import admin_required, enabled_required
from app import db
from datetime import datetime
from .helper_app_functions import helper_basic_app
from app.routes.admin.models import User


@blueprint.route("/get_chat_contanten/<chat_room_number>", methods=["GET"])
@enabled_required
def get_chat_contanten(chat_room_number):
    """
    Holt Chat-Informationen anhand der room_number MIT Benutzerinformationen
    """
    try:
        # ✅ GEÄNDERT: Verwende neue Funktion mit User-Info
        chat, chat_type, error_message = (
            helper_basic_app.find_chat_by_room_number_with_users(
                chat_room_number, current_user
            )
        )

        if chat is None:
            return jsonify(
                {"success": False, "error": error_message, "chat": None, "type": None}
            ), (403 if error_message == "Keine Berechtigung" else 404)

        return jsonify(
            {
                "success": True,
                "chat": chat,  # ✅ Enthält jetzt User-Info!
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
    Holt Chat-Nachrichten MIT Benutzerinformationen
    """
    try:
        # Prüfe erst ob User Zugriff auf diesen Chat hat
        chat, chat_type, error_message = (
            helper_basic_app.find_chat_by_room_number_with_users(
                chat_room_number, current_user
            )
        )

        if chat is None:
            return jsonify(
                {"success": False, "error": error_message, "messages": []}
            ), (403 if error_message == "Keine Berechtigung" else 404)
        else:
            # ✅ GEÄNDERT: Verwende neue Funktion mit User-Info
            all_messages = helper_basic_app.get_all_messages_from_chat_room_with_users(
                chat_room_number
            )
            print(
                f"📨 {len(all_messages)} Nachrichten aus Raum {chat_room_number} mit User-Info geladen"
            )
            current_time = helper_basic_app.get_current_time()
            return jsonify(
                {
                    "success": True,
                    "messages": all_messages,  # ✅ Enthält jetzt username, is_admin, etc.!
                    "room_number": chat_room_number,
                    "current_time": current_time.isoformat(),
                    "message_count": len(all_messages),
                }
            )

    except Exception as e:
        print(f"❌ Fehler in get_chat_messages: {e}")
        return jsonify({"success": False, "error": "Serverfehler", "messages": []}), 500


@blueprint.route("/api/chat_rooms", methods=["GET"])
@enabled_required
def api_chat_rooms():
    """
    API Endpoint für alle User-Chats MIT Benutzerinformationen
    """
    try:
        # ✅ GEÄNDERT: Verwende neue Funktion mit User-Info
        all_my_chats = helper_basic_app.get_all_my_chats_with_users(current_user)

        chats_data = []
        for chat in all_my_chats:
            if chat["type"] == "group":  # Group Chat
                chats_data.append(
                    {
                        "room_number": chat["chat_room_number"],
                        "name": chat["group_name"],
                        "type": "group",
                        "last_message": chat["last_message"],
                        "last_message_date": chat["last_message_date"],
                        "creator_username": chat.get("creator_username"),  # ✅ NEU!
                        "member_count": len(
                            chat.get("members_with_names", [])
                        ),  # ✅ NEU!
                    }
                )
            else:  # Normal Chat
                chats_data.append(
                    {
                        "room_number": chat["chat_room_number"],
                        "name": chat.get(
                            "display_name", "Chat"
                        ),  # ✅ NEU: Schöner Name!
                        "type": "normal",
                        "last_message": chat["last_message"],
                        "last_message_date": chat["last_message_date"],
                        "other_username": chat.get("other_username"),  # ✅ NEU!
                        "user_a_username": chat.get("user_a_username"),  # ✅ NEU!
                        "user_b_username": chat.get("user_b_username"),  # ✅ NEU!
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
    Gibt Status-Informationen über einen Chat-Raum zurück MIT User-Info
    """
    try:
        # ✅ GEÄNDERT: Verwende neue Funktion mit User-Info
        chat, chat_type, error_message = (
            helper_basic_app.find_chat_by_room_number_with_users(
                chat_room_number, current_user
            )
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
                "current_user": {  # ✅ NEU!
                    "id": current_user.id,
                    "username": current_user.username,
                    "is_admin": getattr(current_user, "is_admin", False),
                },
                "chat_info": chat,  # ✅ Enthält jetzt alle User-Informationen!
            }
        )

    except Exception as e:
        print(f"❌ Fehler in api_room_status: {e}")
        return (
            jsonify({"success": False, "error": "Serverfehler", "has_access": False}),
            500,
        )


# ✅ NEU: Route für das Senden von Nachrichten mit User-Info
@blueprint.route("/send_message", methods=["POST"])
@enabled_required
def send_message():
    """
    Sendet eine Nachricht und gibt sie mit User-Info zurück
    """
    try:
        data = request.get_json()

        if not data or not data.get("message") or not data.get("chat_room_number"):
            return jsonify({"success": False, "error": "Unvollständige Daten"}), 400

        # Prüfe Berechtigung für diesen Raum
        chat, chat_type, error_message = (
            helper_basic_app.find_chat_by_room_number_with_users(
                data["chat_room_number"], current_user
            )
        )

        if chat is None:
            return jsonify({"success": False, "error": error_message}), (
                403 if error_message == "Keine Berechtigung" else 404
            )

        # Nachricht speichern mit User-Info
        saved_message = helper_basic_app.safe_new_message_with_user_info(
            data["chat_room_number"],
            chat_type,
            chat.get("id"),
            data["message"],
            current_user,
        )

        if saved_message:
            return jsonify(
                {
                    "success": True,
                    "message": saved_message,  # ✅ Enthält username, is_admin, etc.!
                }
            )
        else:
            return jsonify({"success": False, "error": "Fehler beim Speichern"}), 500

    except Exception as e:
        print(f"❌ Fehler in send_message: {e}")
        return jsonify({"success": False, "error": "Serverfehler"}), 500


@blueprint.route("/api/create_new_group_chat", methods=["POST"])
@enabled_required
def create_new_group_chat():
    try:
        data = request.get_json()
        group_name = data.get("group_name")
        new_group_chat = helper_basic_app.create_new_group_chat(
            group_name, current_user
        )
        all_users = User.query.filter(User.id != current_user.id).all()
        users_dict = [user.to_dict() for user in all_users]

        return jsonify(
            {
                "success": True,
                "group_chat": new_group_chat.to_dict(),
                "all_users": users_dict,
            }
        )
    except Exception as e:
        print(f"❌ Fehler in create_new_group_chat: {e}")
        app_logger.error(f"❌ Fehler in create_new_group_chat: {e}")
        return jsonify({"success": False, "error": "Serverfehler"}), 500


@blueprint.route("/api/add_member_to_group_chat", methods=["POST"])
@enabled_required
def add_member_to_group_chat():
    success = False
    added_users = []
    error_message = []
    try:
        data = request.get_json()
        group_chat_id = data.get("group_chat_id")
        all_user_id = data.get("all_user_id")

        success, added_users, error_message = helper_basic_app.add_group_chat_member(
            group_chat_id, all_user_id
        )

        return jsonify(
            {
                "success": success,
                "added_users": added_users,
                "error_message": error_message,
                "added_count": len(added_users),
            }
        )
    except Exception as e:
        print(f"❌ Fehler in add_member_to_group_chat: {e}")
        app_logger.error(f"❌ Fehler in add_member_to_group_chat: {e}")
        return (
            jsonify(
                {
                    "success": success,
                    "added_users": added_users,
                    "error_message": error_message,
                }
            ),
            500,
        )


# ✅ NEU: Route für User-Info-Lookup
@blueprint.route("/api/user_info/<int:user_id>", methods=["GET"])
@enabled_required
def api_user_info(user_id):
    """
    Holt Benutzerinformationen für eine User ID
    """
    try:
        user_info = helper_basic_app.get_user_info(user_id)
        return jsonify({"success": True, "user": user_info})

    except Exception as e:
        print(f"❌ Fehler in api_user_info: {e}")
        return jsonify({"success": False, "error": "Serverfehler"}), 500


@blueprint.route("/api/delete_messages_room/<chat_room_number>", methods=["DELETE"])
@admin_required
def api_delete_messages_room(chat_room_number):
    """
    Löscht alle Nachrichten aus einem Chat-Raum (nur Admin)
    """
    try:
        deleted_count = helper_basic_app.delete_all_messages_from_room_simple(
            chat_room_number
        )

        return jsonify(
            {
                "success": True,
                "message": f"Alle Nachrichten aus Raum {chat_room_number} gelöscht",
                "deleted_count": deleted_count,
                "room_number": chat_room_number,
            }
        )

    except Exception as e:
        print(f"❌ Fehler beim Löschen der Nachrichten: {e}")
        return (
            jsonify(
                {"success": False, "error": "Serverfehler beim Löschen der Nachrichten"}
            ),
            500,
        )


@blueprint.route("/api/admin/list_group_chats", methods=["GET"])
@admin_required
def api_admin_list_group_chats():
    """
    Listet alle Gruppenchats für Admin-Verwaltung auf
    """
    try:
        group_chats = helper_basic_app.get_all_group_chats_for_admin()

        return jsonify(
            {"success": True, "groups": group_chats, "count": len(group_chats)}
        )

    except Exception as e:
        print(f"❌ Fehler in api_admin_list_group_chats: {e}")
        return (
            jsonify(
                {"success": False, "error": "Serverfehler beim Laden der Gruppenchats"}
            ),
            500,
        )
