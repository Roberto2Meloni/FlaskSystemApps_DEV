# apps/BasicChat/socketio_events.py - KORRIGIERTE VERSION

from app import socketio
from flask_socketio import emit, join_room, leave_room
from flask_login import current_user
from flask import request

# Aktueller Raum des Users (pro Session)
user_current_rooms = {}

print("✅ BasicChat Socket.IO Events werden registriert...")


@socketio.on("BasicChat_join_chat_room")
def handle_join_chat_room(data):
    """
    User tritt einem spezifischen Chat-Raum bei
    Event: BasicChat_join_chat_room
    """
    room_number = data.get("room_number")
    if not room_number:
        print("❌ Keine room_number angegeben")
        return

    # Username ermitteln
    if current_user.is_authenticated:
        username = current_user.username
        user_id = current_user.id
    else:
        username = f"Gast_{request.sid[:6]}"
        user_id = None

    # Alten Raum verlassen (falls vorhanden)
    # Diese Funktion wurde aus Desing gründen auskomentiert aber beibehalten, da dies als Beispiel Code gnutzt wird
    # old_room = user_current_rooms.get(request.sid)
    # if old_room:
    #     leave_room(old_room)
    #     print(f"👤 {username} hat Raum {old_room} verlassen")

    #     # ✅ KORRIGIERT: Standard emit() verwenden
    #     emit(
    #         "BasicChat_user_left_room",
    #         {"username": username, "room_number": old_room, "user_id": user_id},
    #         room=old_room,
    #         include_self=False,
    #     )

    # Neuem Raum beitreten
    join_room(room_number)
    user_current_rooms[request.sid] = room_number
    print(f"👤 {username} ist Raum {room_number} beigetreten")

    emit(
        "BasicChat_user_joined_room",
        {"username": username, "room_number": room_number, "user_id": user_id},
        room=room_number,
        include_self=False,
    )

    # Bestätigung an den User selbst
    emit(
        "BasicChat_room_joined_successfully",
        {
            "room_number": room_number,
            "message": f"Du bist Raum {room_number} beigetreten",
        },
    )


@socketio.on("BasicChat_leave_chat_room")
def handle_leave_chat_room(data):
    """
    User verlässt den aktuellen Chat-Raum explizit
    Event: BasicChat_leave_chat_room
    """
    current_room = user_current_rooms.get(request.sid)
    if not current_room:
        return

    # Username ermitteln
    if current_user.is_authenticated:
        username = current_user.username
        user_id = current_user.id
    else:
        username = f"Gast_{request.sid[:6]}"
        user_id = None

    # Raum verlassen
    leave_room(current_room)
    del user_current_rooms[request.sid]
    print(f"👤 {username} hat Raum {current_room} verlassen")

    # ✅ KORRIGIERT: Standard emit() verwenden
    emit(
        "BasicChat_user_left_room",
        {"username": username, "room_number": current_room, "user_id": user_id},
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
    Event: BasicChat_get_room_info
    """
    current_room = user_current_rooms.get(request.sid)

    # ✅ KORRIGIERT: Standard emit() verwenden
    emit(
        "BasicChat_room_info_response",
        {"current_room": current_room, "is_in_room": current_room is not None},
    )


@socketio.on("BasicChat_do_the_harlemshake")
def handle_do_the_harlemshake(data):
    """
    Harlemshake-Befehl - bleibt global
    Event: BasicChat_do_the_harlemshake
    """
    name = data.get("name", "Unbekannt")
    is_admin = data.get("isAdmin", False)
    print(f"🕺 Harlemshake Befehl von {name}. Admin Status: {is_admin}")

    # Global an alle senden (ohne App-Prefix für globale Events)
    emit(
        "BasicChat_do_the_harlemshake_reply",
        {"sender": name, "isAdmin": is_admin},
        broadcast=True,
    )


# =============================================================================
# ✅ KORREKT: Disconnect Hook registrieren (NICHT als Socket.IO Event!)
# =============================================================================


def basicchat_disconnect_cleanup(request_sid, user_data):
    """
    BasicChat-spezifisches Disconnect-Cleanup
    Diese Funktion wird vom SocketIO Manager aufgerufen
    """
    print(f"🧹 BasicChat disconnect cleanup für SID: {request_sid}")

    current_room = user_current_rooms.get(request_sid)
    if current_room:
        # Username aus user_data holen
        if user_data and user_data.get("is_authenticated"):
            username = user_data["username"]
            user_id = user_data["user_id"]
        else:
            username = f"User_{request_sid[:6]}"
            user_id = None

        # Anderen im Raum mitteilen
        socketio.emit(
            "BasicChat_user_left_room",
            {
                "username": username,
                "room_number": current_room,
                "user_id": user_id,
                "reason": "disconnected",
            },
            room=current_room,
        )

        # Aus Dictionary entfernen
        del user_current_rooms[request_sid]
        print(f"👤 {username} disconnected und verließ Chat-Raum {current_room}")
    else:
        print(f"👤 User {request_sid} disconnected (war in keinem Raum)")


def register_basicchat_hooks():
    """
    Registriert BasicChat Hooks beim SocketIO Manager
    """
    print("🔗 Registriere BasicChat Disconnect-Hooks...")

    try:
        from app.socketio_manager import get_socketio_manager

        manager = get_socketio_manager()
        if manager:
            # ✅ Hook beim Manager registrieren
            manager.register_disconnect_hook("BasicChat", basicchat_disconnect_cleanup)
            print("✅ BasicChat disconnect hook erfolgreich registriert")
        else:
            print("❌ SocketIO Manager nicht verfügbar für BasicChat")

    except Exception as e:
        print(f"❌ Fehler beim Registrieren der BasicChat Hooks: {e}")


# =============================================================================
# OPTIONAL: Manager-basierte Events (falls Sie emit_to_app nutzen möchten)
# =============================================================================


def use_manager_events():
    """
    Beispiel wie Sie den SocketIO Manager für emit_to_app nutzen können
    """
    try:
        from app.socketio_manager import get_socketio_manager

        manager = get_socketio_manager()

        if manager and hasattr(manager, "emit_to_app"):
            # Dann können Sie manager.emit_to_app() verwenden
            return manager
        else:
            return None
    except Exception as e:
        print(f"❌ Fehler beim Abrufen des SocketIO Managers: {e}")
        return None


# Alternative emit-Funktion mit Manager
def emit_with_manager(event_name, data, **kwargs):
    """
    Wrapper-Funktion für emit mit optionalem Manager
    """
    manager = use_manager_events()

    if manager and hasattr(manager, "emit_to_app"):
        # Manager-Version verwenden
        manager.emit_to_app("BasicChat", event_name, data, **kwargs)
    else:
        # Standard emit verwenden
        emit(f"BasicChat_{event_name}", data, **kwargs)


# =============================================================================
# HOOK-REGISTRIERUNG beim Import
# =============================================================================

# ✅ Hooks automatisch registrieren wenn das Modul geladen wird
register_basicchat_hooks()

print("✅ BasicChat Socket.IO Events registriert")

# =============================================================================
# ZUSÄTZLICHE VERBESSERUNGEN (Optional)
# =============================================================================


# def get_user_current_room(sid):
#     """Hilfsfunktion: Aktuellen Raum eines Users abrufen"""
#     return user_current_rooms.get(sid)


# def set_user_current_room(sid, room):
#     """Hilfsfunktion: Aktuellen Raum eines Users setzen"""
#     user_current_rooms[sid] = room


# def remove_user_from_rooms(sid):
#     """Hilfsfunktion: User aus allen Räumen entfernen"""
#     if sid in user_current_rooms:
#         del user_current_rooms[sid]


# def get_all_users_in_room(room_number):
#     """Hilfsfunktion: Alle User in einem Raum abrufen"""
#     return [sid for sid, room in user_current_rooms.items() if room == room_number]


# def get_room_statistics():
#     """Debug-Funktion: Raum-Statistiken abrufen"""
#     from collections import Counter

#     room_counts = Counter(user_current_rooms.values())

#     return {
#         "total_users": len(user_current_rooms),
#         "total_rooms": len(room_counts),
#         "room_distribution": dict(room_counts),
#         "users_per_room": dict(room_counts),
#     }


# # =============================================================================
# # DEBUG-FUNKTIONEN
# # =============================================================================


# def debug_basicchat_status():
#     """Debug-Funktion für BasicChat Status"""
#     print("=== BasicChat SocketIO Status ===")
#     print(f"Aktive User-Sessions: {len(user_current_rooms)}")
#     print(f"Raum-Verteilung: {get_room_statistics()}")

#     # Manager-Status
#     try:
#         from app.socketio_manager import get_socketio_manager

#         manager = get_socketio_manager()
#         if manager:
#             basicchat_hooks = [
#                 h for h in manager.disconnect_hooks if h["app_name"] == "BasicChat"
#             ]
#             print(f"Registrierte BasicChat Hooks: {len(basicchat_hooks)}")
#         else:
#             print("❌ SocketIO Manager nicht verfügbar")
#     except Exception as e:
#         print(f"❌ Fehler beim Manager-Check: {e}")


# # Export für externe Nutzung
# __all__ = [
#     "basicchat_disconnect_cleanup",
#     "register_basicchat_hooks",
#     "get_user_current_room",
#     "set_user_current_room",
#     "remove_user_from_rooms",
#     "get_room_statistics",
#     "debug_basicchat_status",
# ]
