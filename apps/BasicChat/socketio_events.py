# apps/BasicChat/socketio_events.py - KORRIGIERTE VERSION mit Benutzerinformationen
from app import socketio
from flask_socketio import emit, join_room, leave_room
from flask_login import current_user
from flask import request
from app.helper_functions.helper_db_file import check_if_user_has_admin_rights
from app.routes.admin.models import User  # Oder dein User Model Pfad
from . import app_logger


from app import app


from .helper_app_functions import helper_basic_app


# Aktueller Raum des Users (pro Session)
user_current_rooms = {}

app_logger.info("✅ BasicChat Socket.IO Events werden registriert...")


@socketio.on("BasicChat_join_chat_room")
def handle_join_chat_room(data):
    """
    User tritt einem spezifischen Chat-Raum bei
    Event: BasicChat_join_chat_room
    """
    room_number = data.get("room_number")
    if not room_number:
        app_logger.error("❌ Keine room_number angegeben")
        return

    # Username ermitteln
    if current_user.is_authenticated:
        username = current_user.username
        user_id = current_user.id
        is_admin = getattr(current_user, "is_admin", False)
    else:
        username = f"Gast_{request.sid[:6]}"
        user_id = None
        is_admin = False

    # ✅ NEU: Berechtigung für Raum prüfen
    chat, chat_type, error_message = (
        helper_basic_app.find_chat_by_room_number_with_users(room_number, current_user)
    )

    if chat is None:
        emit(
            "BasicChat_join_room_error",
            {"error": error_message, "room_number": room_number},
        )
        return

    # Neuem Raum beitreten
    join_room(room_number)
    user_current_rooms[request.sid] = room_number

    app_logger.debug(f"👤 {username} ist Raum {room_number} beigetreten")

    # DEBUG: Anzahl und Namen der User im Raum anzeigen
    users_in_room = []
    for sid, room in user_current_rooms.items():
        if room == room_number:
            users_in_room.append(f"SID_{sid[:6]}")

    app_logger.debug(
        f"🏠 DEBUG: Raum {room_number} hat jetzt {len(users_in_room)} User"
    )
    app_logger.debug(f"🏠 DEBUG: User im Raum: {', '.join(users_in_room)}")

    # ✅ ERWEITERT: Mehr User-Info senden
    emit(
        "BasicChat_user_joined_room",
        {
            "username": username,
            "room_number": room_number,
            "user_id": user_id,
            "is_admin": is_admin,  # ✅ NEU!
            "user_exists": True,  # ✅ NEU!
        },
        room=room_number,
        include_self=False,
    )

    # Bestätigung an den User selbst
    emit(
        "BasicChat_room_joined_successfully",
        {
            "room_number": room_number,
            "message": f"Du bist Raum {room_number} beigetreten",
            "chat_info": chat,  # ✅ NEU: Chat-Info mit User-Details!
        },
    )


@socketio.on("BasicChat_leave_chat_room")
def handle_leave_chat_room(data):
    """
    User verlässt den aktuellen Chat-Raum explizit
    """
    current_room = user_current_rooms.get(request.sid)
    if not current_room:
        return

    # Username ermitteln
    if current_user.is_authenticated:
        username = current_user.username
        user_id = current_user.id
        is_admin = getattr(current_user, "is_admin", False)
    else:
        username = f"Gast_{request.sid[:6]}"
        user_id = None
        is_admin = False

    # Raum verlassen
    leave_room(current_room)
    del user_current_rooms[request.sid]

    app.logger.debug(f"👤 {username} hat Raum {current_room} verlassen")

    # ✅ ERWEITERT: Mehr User-Info senden
    emit(
        "BasicChat_user_left_room",
        {
            "username": username,
            "room_number": current_room,
            "user_id": user_id,
            "is_admin": is_admin,  # ✅ NEU!
        },
        room=current_room,
        include_self=False,
    )

    # Bestätigung an den User selbst
    emit(
        "BasicChat_room_left_successfully",
        {
            "room_number": current_room,
            "message": f"Du hast Raum {current_room} verlassen",
        },
    )


@socketio.on("BasicChat_get_room_info")
def handle_get_room_info(data):
    """
    Gibt Informationen über den aktuellen Raum zurück
    """
    current_room = user_current_rooms.get(request.sid)

    # ✅ NEU: Wenn in Raum, dann detaillierte Info laden
    chat_info = None
    if current_room and current_user.is_authenticated:
        chat, chat_type, error_message = (
            helper_basic_app.find_chat_by_room_number_with_users(
                current_room, current_user
            )
        )
        if chat:
            chat_info = chat

    emit(
        "BasicChat_room_info_response",
        {
            "current_room": current_room,
            "is_in_room": current_room is not None,
            "chat_info": chat_info,  # ✅ NEU: Detaillierte Chat-Info!
        },
    )


@socketio.on("BasicChat_do_the_harlemshake")
def handle_do_the_harlemshake(data):
    """
    Harlemshake-Befehl - bleibt global
    """
    name = data.get("name", "Unbekannt")
    this_user = User.query.filter_by(username=name).first()
    is_admin = check_if_user_has_admin_rights(app, this_user.id) if this_user else False

    app.logger.debug(f"🕺 Harlemshake Befehl von {name}. Admin Status: {is_admin}")

    emit(
        "BasicChat_do_the_harlemshake_reply",
        {"sender": name, "isAdmin": is_admin},
        broadcast=True,
    )


@socketio.on("BasicChat_send_message")
def handle_send_message(data):
    """
    ✅ KORRIGIERT: Sendet Nachricht MIT Benutzerinformationen
    """
    this_message = data.get("message")
    this_room_number = data.get("room_number")
    current_time = helper_basic_app.get_current_time()

    app_logger.debug(
        f"Neue Nachricht | Raum: {this_room_number} | User: {current_user.username} | Nachricht: {this_message}"
    )
    app_logger.debug("🔍 DEBUG: Prüfe Berechtigung...")

    try:
        # ✅ GEÄNDERT: Verwende neue Funktion mit User-Info
        chat, chat_type, error_message = (
            helper_basic_app.find_chat_by_room_number_with_users(
                this_room_number, current_user
            )
        )
        app_logger.debug(
            f"🔍 DEBUG: Berechtigung geprüft - chat: {chat is not None}, error: {error_message}"
        )
    except Exception as e:
        app.logger.error(f"❌ FEHLER bei Berechtigung: {e}")
        emit(
            "BasicChat_client_message_recieved",
            {"success": False, "error": "Serverfehler bei Berechtigung"},
        )
        return

    if chat is None:
        app_logger.debug("🔍 DEBUG: Sende Fehler-Response...")
        emit(
            "BasicChat_client_message_recieved",
            {"success": False, "error": error_message},
        )
    else:
        app_logger.debug("🔍 DEBUG: Speichere Nachricht...")
        try:
            # ✅ GEÄNDERT: Verwende neue Funktion mit User-Info
            json_new_message = helper_basic_app.safe_new_message_with_user_info(
                this_room_number, chat_type, chat["id"], this_message, current_user
            )

            if json_new_message:
                app_logger.debug(
                    f"🔍 DEBUG: Nachricht mit User-Info gespeichert, sende an Room {this_room_number}..."
                )

                # ✅ ERWEITERT: Sende vollständige Nachricht mit User-Info
                emit(
                    "BasicChat_client_message_recieved",
                    {
                        "success": True,
                        "error": "",
                        "message": json_new_message,  # ✅ Enthält jetzt username, is_admin, etc.!
                        "current_time": current_time.isoformat(),
                        "room_number": this_room_number,
                    },
                    room=this_room_number,
                )
                app_logger.debug(
                    "✅ DEBUG: emit() mit User-Info erfolgreich ausgeführt"
                )
            else:
                app_logger.error("❌ DEBUG: Nachricht konnte nicht gespeichert werden")
                emit(
                    "BasicChat_client_message_recieved",
                    {
                        "success": False,
                        "error": "Nachricht konnte nicht gespeichert werden",
                    },
                )

        except Exception as e:
            app_logger.error(f"❌ FEHLER beim Speichern/Senden: {e}")
            emit(
                "BasicChat_client_message_recieved", {"success": False, "error": str(e)}
            )


# ✅ NEU: Event für User-Info Lookup
@socketio.on("BasicChat_get_user_info")
def handle_get_user_info(data):
    """
    Holt Benutzerinformationen für eine User-ID
    """
    user_id = data.get("user_id")
    if not user_id:
        emit(
            "BasicChat_user_info_response",
            {"success": False, "error": "Keine user_id angegeben"},
        )
        return

    try:
        user_info = helper_basic_app.get_user_info(user_id)
        emit("BasicChat_user_info_response", {"success": True, "user": user_info})
    except Exception as e:
        app_logger(f"❌ Fehler bei User-Info Lookup: {e}")
        emit(
            "BasicChat_user_info_response", {"success": False, "error": "Serverfehler"}
        )


# =============================================================================
# DISCONNECT CLEANUP (unverändert)
# =============================================================================
def basicchat_disconnect_cleanup(request_sid, user_data):
    """
    BasicChat-spezifisches Disconnect-Cleanup
    """
    app_logger.debug(f"🧹 BasicChat disconnect cleanup für SID: {request_sid}")
    current_room = user_current_rooms.get(request_sid)

    if current_room:
        if user_data and user_data.get("is_authenticated"):
            username = user_data["username"]
            user_id = user_data["user_id"]
            is_admin = user_data.get("is_admin", False)
        else:
            username = f"User_{request_sid[:6]}"
            user_id = None
            is_admin = False

        # ✅ ERWEITERT: Mehr User-Info beim Disconnect
        socketio.emit(
            "BasicChat_user_left_room",
            {
                "username": username,
                "room_number": current_room,
                "user_id": user_id,
                "is_admin": is_admin,  # ✅ NEU!
                "reason": "disconnected",
            },
            room=current_room,
        )

        del user_current_rooms[request_sid]
        app_logger.debug(
            f"👤 {username} disconnected und verließ Chat-Raum {current_room}"
        )
    else:
        app_logger.debug(f"👤 User {request_sid} disconnected (war in keinem Raum)")


def register_basicchat_hooks():
    """
    Registriert BasicChat Hooks beim SocketIO Manager
    """
    app_logger.debug("🔗 Registriere BasicChat Disconnect-Hooks...")
    try:
        from app.socketio_manager import get_socketio_manager

        manager = get_socketio_manager()
        if manager:
            manager.register_disconnect_hook("BasicChat", basicchat_disconnect_cleanup)
            app_logger.info("✅ BasicChat disconnect hook erfolgreich registriert")
        else:
            app_logger.error("❌ SocketIO Manager nicht verfügbar für BasicChat")
    except Exception as e:
        app_logger.error(f"❌ Fehler beim Registrieren der BasicChat Hooks: {e}")


# Hook-Registrierung beim Import
register_basicchat_hooks()
