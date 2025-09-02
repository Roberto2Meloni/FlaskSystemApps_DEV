from app import socketio
from flask_socketio import emit, join_room, leave_room
from flask_login import current_user
from flask import request


# ===== CHAT-SPEZIFISCHE EVENTS (ohne Konflikt mit __init__.py) =====
# Die bestehenden Events (connect, disconnect, ping) bleiben in __init__.py
# Hier definieren wir nur NEUE Events für den Chat


@socketio.on("BasicChat_do_the_harlemshake")
def handle_BasicChat_do_the_harlemshake(data):
    name = data.get("name", "Unbekannt")
    is_admin = data.get("isAdmin", False)

    print(
        f"Harlemshake Befehl von {name}. Admin Status: {is_admin}, senden wir dies an alle"
    )

    emit(
        "BasicChat_do_the_harlemshake_reply",
        {"sender": name, "isAdmin": is_admin},
        broadcast=True,
    )


@socketio.on("BasicChat_send_message")
def handle_BasicChat_send_message(data):
    """
    Behandelt das Senden von Chat-Nachrichten
    Dies ist ein NEUER Event - kein Konflikt mit __init__.py
    """
    print(f"💬 Chat: Nachricht empfangen: {data}")

    if not data or "message" not in data:
        print("❌ Chat: Ungültige Nachricht")
        return

    message = data["message"].strip()
    if not message:
        return

    # Benutzer-Info ermitteln
    if current_user.is_authenticated:
        username = current_user.username
        user_id = current_user.id
    else:
        username = f"Gast_{request.sid[:6]}"
        user_id = None

    print(f"💬 {username}: {message}")

    # Nachricht an ALLE Clients senden (auch an den Sender)
    emit(
        "new_message",
        {
            "message": message,
            "username": username,
            "user_id": user_id,
            "timestamp": data.get("timestamp", "jetzt"),
        },
        broadcast=True,
    )  # broadcast=True sendet an ALLE verbundenen Clients


@socketio.on("BasicChat_join_global_chat")
def handle_BasicChat_join_global_chat():
    """
    Benutzer tritt dem globalen Chat bei
    Dies ist ein NEUER Event - kein Konflikt
    """

    if current_user.is_authenticated:
        username = current_user.username
    else:
        username = f"Gast_{request.sid[:6]}"

    print(f"👤 {username} ist dem globalen Chat beigetreten")

    # # Info an alle in der Room
    # emit(
    #     "user_joined_chat",
    #     {"username": username, "room_id": global_room_id},
    #     room=global_room_id,
    #     include_self=False,
    # )  # include_self=False sendet NICHT an sich selbst
    # Info an alle in der Room
    emit(
        "user_joined_chat",
        {
            "username": username,
        },
        include_self=False,
    )  # include_self=False sendet NICHT an sich selbst
