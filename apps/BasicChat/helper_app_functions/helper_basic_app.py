import os
import json
from ..models import BasicChatGroupChat, BasicChatNormalChat, BasicChatChatMessages
import secrets, string
from app import db, app
from sqlalchemy import or_
from datetime import datetime
from pytz import timezone

# ✅ NEU: User Model Import für Benutzerinformationen
from app.routes.admin.models import User

# Variabeln
root_path = os.getcwd()
config_file_path = os.path.join(
    root_path, "app", "imported_apps", "develop_release", "BasicChat", "app_config.json"
)


def get_current_time():
    return datetime.now(tz=timezone("Europe/Zurich")).replace(second=0, microsecond=0)


def get_app_config():
    try:
        with open(config_file_path, "r", encoding="utf-8") as file:
            return json.load(file)
    except FileNotFoundError:
        return {}


def creat_group_caht_number(existing_group_chat_numbers):
    while True:
        new_number = "".join(
            secrets.choice(string.ascii_letters + string.digits) for _ in range(16)
        )
        if new_number not in existing_group_chat_numbers:
            return new_number


def create_global_group_chat():  # ← KEIN app Parameter mehr!
    """Erstellt globalen Chat falls er nicht existiert"""
    try:
        app.logger.debug("🔍 Prüfe ob globaler Chat existiert...")

        # WICHTIG: no_autoflush für alle Database-Queries!
        with db.session.no_autoflush:
            existing_global_chat = BasicChatGroupChat.query.filter_by(
                group_name="Global"
            ).first()

        if not existing_global_chat:
            app.logger.warning(
                "➕ Globaler Chat existiert nicht! Erstelle neuen Chat..."
            )

            # Alle existierenden Nummern sammeln
            all_numbers = []

            with db.session.no_autoflush:
                all_group_chats = BasicChatGroupChat.query.all()
                all_normal_chats = BasicChatNormalChat.query.all()

            for group_chat in all_group_chats:
                if group_chat.chat_room_number:
                    all_numbers.append(group_chat.chat_room_number)

            for normal_chat in all_normal_chats:
                if normal_chat.chat_room_number:
                    all_numbers.append(normal_chat.chat_room_number)

            # Neue eindeutige Nummer generieren
            new_number = creat_group_caht_number(all_numbers)
            app.logger.debug(f"🔢 Neue globale Chat-Nummer: {new_number}")

            # Globalen Chat erstellen
            new_global_group_chat = BasicChatGroupChat(
                chat_room_number=new_number,
                group_name="Global",
                group_admins="",  # ← String statt Liste!
                group_members="*",  # Alle Benutzer
                created_by_user_id=1,  # Admin User ID
            )

            db.session.add(new_global_group_chat)
            db.session.commit()

            app.logger.info("✅ Globaler Chat erfolgreich erstellt!")

        else:
            app.logger.info(
                "ℹ️ Globaler Chat existiert bereits - keine Aktion erforderlich"
            )

    except Exception as e:
        app.logger.error(f"❌ Fehler beim Erstellen des globalen Chats: {e}")
        db.session.rollback()
        raise


def create_global_group_chat_safe():
    """Sichere Version mit zusätzlichem Error-Handling"""
    try:
        # Session zurücksetzen vor der Operation
        db.session.rollback()

        # Hauptfunktion ausführen
        create_global_group_chat()

    except Exception as e:
        app.logger.critical(
            f"❌ Kritischer Fehler in create_global_group_chat_safe: {e}"
        )

        # Fallback: Einfachen globalen Chat erstellen
        try:
            db.session.rollback()

            simple_number = "".join(
                secrets.choice(string.ascii_letters + string.digits) for _ in range(16)
            )

            fallback_chat = BasicChatGroupChat(
                chat_room_number=simple_number,
                group_name="Global",
                group_admins="1",
                group_members="*",
                created_by_user_id=1,
            )

            db.session.add(fallback_chat)
            db.session.commit()

            app.logger.debug("✅ Fallback globaler Chat erstellt")

        except Exception as fallback_error:
            app.logger.error(f"❌ Auch Fallback fehlgeschlagen: {fallback_error}")
            db.session.rollback()


def get_global_chat_room_id():
    """Holt die Room-ID des globalen Chats"""
    try:
        with db.session.no_autoflush:
            global_chat = BasicChatGroupChat.query.filter_by(
                group_name="Global"
            ).first()

        if global_chat:
            return global_chat.chat_room_number
        else:
            return None

    except Exception as e:
        app.logger.error(f"❌ Fehler beim Abrufen der globalen Chat-ID: {e}")
        return None


def get_all_my_chats(current_user):
    """
    Holt alle Chats für den aktuellen User
    """
    # Group Chats wo User Mitglied oder Admin ist
    group_chats = BasicChatGroupChat.query.filter(
        or_(
            BasicChatGroupChat.group_members == "*",  # Öffentliche Chats
            BasicChatGroupChat.group_admins.contains(str(current_user.id)),
            BasicChatGroupChat.group_members.contains(str(current_user.id)),
        )
    ).all()

    # Normal Chats wo User teilnimmt
    normal_chats = BasicChatNormalChat.query.filter(
        or_(
            BasicChatNormalChat.a_user_id == current_user.id,
            BasicChatNormalChat.b_user_id == current_user.id,
        )
    ).all()

    return group_chats + normal_chats


# ✅ NEU: Erweiterte Version mit Benutzerinformationen
def get_all_my_chats_with_users(current_user):
    """
    Holt alle Chats für den aktuellen User MIT Benutzerinformationen
    """
    try:
        all_chats = []

        # 1. Group Chats wo User Mitglied oder Admin ist
        group_chats = BasicChatGroupChat.query.filter(
            or_(
                BasicChatGroupChat.group_members == "*",  # Öffentliche Chats
                BasicChatGroupChat.group_admins.contains(str(current_user.id)),
                BasicChatGroupChat.group_members.contains(str(current_user.id)),
            )
        ).all()

        for chat in group_chats:
            chat_dict = chat.to_dict()
            chat_dict["type"] = "group"

            # Creator-Info hinzufügen
            if chat.created_by_user_id:
                creator = User.query.get(chat.created_by_user_id)
                chat_dict["creator_username"] = (
                    creator.username
                    if creator
                    else f"Gelöschter User (ID: {chat.created_by_user_id})"
                )

            # Member-Liste mit Usernamen (falls nicht "*")
            if chat.group_members and chat.group_members != "*":
                member_ids = [
                    int(id.strip())
                    for id in chat.group_members.split(",")
                    if id.strip().isdigit()
                ]
                members = (
                    User.query.filter(User.id.in_(member_ids)).all()
                    if member_ids
                    else []
                )
                chat_dict["members_with_names"] = [
                    {"id": user.id, "username": user.username} for user in members
                ]
            else:
                chat_dict["members_with_names"] = []  # Öffentlicher Chat

            all_chats.append(chat_dict)

        # 2. Normal Chats wo User teilnimmt
        normal_chats = BasicChatNormalChat.query.filter(
            or_(
                BasicChatNormalChat.a_user_id == current_user.id,
                BasicChatNormalChat.b_user_id == current_user.id,
            )
        ).all()

        for chat in normal_chats:
            chat_dict = chat.to_dict()
            chat_dict["type"] = "normal"

            # Andere User-Info hinzufügen
            other_user_id = (
                chat.b_user_id if chat.a_user_id == current_user.id else chat.a_user_id
            )
            other_user = User.query.get(other_user_id)

            user_a = User.query.get(chat.a_user_id)
            user_b = User.query.get(chat.b_user_id)

            chat_dict["other_user_id"] = other_user_id
            chat_dict["other_username"] = (
                other_user.username
                if other_user
                else f"Gelöschter User (ID: {other_user_id})"
            )
            chat_dict["display_name"] = chat_dict["other_username"]

            chat_dict["user_a_username"] = (
                user_a.username if user_a else f"Gelöschter User (ID: {chat.a_user_id})"
            )
            chat_dict["user_b_username"] = (
                user_b.username if user_b else f"Gelöschter User (ID: {chat.b_user_id})"
            )

            all_chats.append(chat_dict)

        return all_chats

    except Exception as e:
        app.logger.error(f"❌ Fehler beim Laden der Chats mit Users: {e}")
        return []


def find_chat_by_room_number(chat_room_number, current_user):
    """
    Findet einen Chat anhand der room_number und prüft Berechtigungen
    Rückgabe: chat, chat_type, error_message
    """
    # Erst in Group Chats suchen
    group_chat = BasicChatGroupChat.query.filter_by(
        chat_room_number=chat_room_number
    ).first()

    if group_chat:
        # Prüfe Berechtigung für Group Chat
        if (
            group_chat.group_members == "*"
            or str(current_user.id) in (group_chat.group_admins or "")
            or str(current_user.id) in (group_chat.group_members or "")
        ):
            return group_chat.to_dict(), "group", ""
        else:
            return None, None, "Keine Berechtigung"

    # Dann in Normal Chats suchen
    normal_chat = BasicChatNormalChat.query.filter_by(
        chat_room_number=chat_room_number
    ).first()

    if normal_chat:
        # Prüfe Berechtigung für Normal Chat
        if (
            current_user.id == normal_chat.a_user_id
            or current_user.id == normal_chat.b_user_id
        ):
            return normal_chat.to_dict(), "normal", ""
        else:
            return None, None, "Keine Berechtigung"

    return None, None, "Chat nicht gefunden"


# ✅ NEU: Erweiterte Version mit Benutzerinformationen
def find_chat_by_room_number_with_users(chat_room_number, current_user):
    """
    Findet einen Chat MIT Benutzerinformationen und prüft Berechtigung
    Rückgabe: chat_dict, chat_type, error_message
    """
    try:
        # Erst in Group Chats suchen
        group_chat = BasicChatGroupChat.query.filter_by(
            chat_room_number=chat_room_number
        ).first()

        if group_chat:
            # Berechtigung prüfen
            if (
                group_chat.group_members == "*"
                or str(current_user.id) in (group_chat.group_admins or "")
                or str(current_user.id) in (group_chat.group_members or "")
            ):
                chat_dict = group_chat.to_dict()

                # Creator-Info hinzufügen
                if group_chat.created_by_user_id:
                    creator = User.query.get(group_chat.created_by_user_id)
                    chat_dict["creator_username"] = (
                        creator.username
                        if creator
                        else f"Gelöschter User (ID: {group_chat.created_by_user_id})"
                    )

                # Member-Liste mit Usernamen (falls nicht "*")
                if group_chat.group_members and group_chat.group_members != "*":
                    member_ids = [
                        int(id.strip())
                        for id in group_chat.group_members.split(",")
                        if id.strip().isdigit()
                    ]
                    members = (
                        User.query.filter(User.id.in_(member_ids)).all()
                        if member_ids
                        else []
                    )
                    chat_dict["members_with_names"] = [
                        {"id": user.id, "username": user.username} for user in members
                    ]
                else:
                    chat_dict["members_with_names"] = []  # Öffentlicher Chat

                # Admin-Liste mit Usernamen
                if group_chat.group_admins:
                    admin_ids = [
                        int(id.strip())
                        for id in group_chat.group_admins.split(",")
                        if id.strip().isdigit()
                    ]
                    admins = (
                        User.query.filter(User.id.in_(admin_ids)).all()
                        if admin_ids
                        else []
                    )
                    chat_dict["admins_with_names"] = [
                        {"id": user.id, "username": user.username} for user in admins
                    ]
                else:
                    chat_dict["admins_with_names"] = []

                return chat_dict, "group", ""
            else:
                return None, None, "Keine Berechtigung"

        # Dann in Normal Chats suchen
        normal_chat = BasicChatNormalChat.query.filter_by(
            chat_room_number=chat_room_number
        ).first()

        if normal_chat:
            # Berechtigung prüfen
            if (
                current_user.id == normal_chat.a_user_id
                or current_user.id == normal_chat.b_user_id
            ):
                chat_dict = normal_chat.to_dict()

                # Beide User-Info hinzufügen
                user_a = User.query.get(normal_chat.a_user_id)
                user_b = User.query.get(normal_chat.b_user_id)

                chat_dict["user_a_username"] = (
                    user_a.username
                    if user_a
                    else f"Gelöschter User (ID: {normal_chat.a_user_id})"
                )
                chat_dict["user_b_username"] = (
                    user_b.username
                    if user_b
                    else f"Gelöschter User (ID: {normal_chat.b_user_id})"
                )

                # Display-Name für aktuellen User
                if current_user.id == normal_chat.a_user_id:
                    chat_dict["display_name"] = chat_dict["user_b_username"]
                else:
                    chat_dict["display_name"] = chat_dict["user_a_username"]

                return chat_dict, "normal", ""
            else:
                return None, None, "Keine Berechtigung"

        return None, None, "Chat nicht gefunden"

    except Exception as e:
        app.logger.error(f"❌ Fehler beim Suchen des Chats mit Users: {e}")
        return None, None, "Serverfehler"


def find_chat_messages_by_room_number(chat_room_number, current_user):
    chat, type, error_message = find_chat_by_room_number(chat_room_number, current_user)
    if chat:
        all_messages = BasicChatChatMessages.query.filter_by(
            chat_room_number=chat_room_number
        ).all()
        return all_messages, type, error_message
    else:
        return None, None, error_message


def safe_new_message(chat_room_number, chat_type, chat_id, message, current_user):
    """
    Gebe dict von Nachricht zurück, damit dies emited werden kann
    """
    new_message = BasicChatChatMessages(
        message=message,
        user_id=current_user.id,
        chat_room_number=chat_room_number,
        chat_type=chat_type,
    )
    if chat_type == "group":
        new_message.group_chat_id = chat_id
    else:
        new_message.normal_chat_id = chat_id

    db.session.add(new_message)
    db.session.commit()

    return new_message.to_dict()


# ✅ NEU: Erweiterte Version mit Benutzerinformationen
def safe_new_message_with_user_info(
    chat_room_number, chat_type, chat_id, message, current_user
):
    """
    Speichert Nachricht und gibt sie mit User-Info zurück
    """
    try:
        new_message = BasicChatChatMessages(
            message=message,
            user_id=current_user.id,
            chat_room_number=chat_room_number,
            chat_type=chat_type,
            created_at=get_current_time(),
        )

        if chat_type == "group":
            new_message.group_chat_id = chat_id
        else:
            new_message.normal_chat_id = chat_id

        db.session.add(new_message)
        db.session.commit()

        # User-Info für Response holen
        user = User.query.get(current_user.id)

        # Message mit User-Info zurückgeben
        message_dict = new_message.to_dict()
        message_dict.update(
            {
                "username": (
                    user.username
                    if user
                    else f"Unbekannter User (ID: {current_user.id})"
                ),
                "user_exists": user is not None,
                "is_admin": getattr(user, "is_admin", False) if user else False,
                "user_avatar": getattr(user, "avatar_url", None) if user else None,
            }
        )

        return message_dict

    except Exception as e:
        app.logger.error(f"❌ Fehler beim Speichern der Nachricht mit User-Info: {e}")
        db.session.rollback()
        return None


def get_all_messages_from_chat_room(chat_room_number):
    """
    Holt alle Nachrichten aus einem Chat-Raum (OHNE User-Info)
    """
    all_messages = (
        BasicChatChatMessages.query.filter_by(chat_room_number=chat_room_number)
        .order_by(BasicChatChatMessages.created_at)
        .all()
    )
    return [message.to_dict() for message in all_messages]


# ✅ NEU: Erweiterte Version mit Benutzerinformationen
def get_all_messages_from_chat_room_with_users(chat_room_number):
    """
    Holt alle Nachrichten aus einem Chat-Raum MIT Benutzerinformationen
    """
    try:
        # Nachrichten holen
        messages = (
            BasicChatChatMessages.query.filter_by(chat_room_number=chat_room_number)
            .order_by(BasicChatChatMessages.created_at)
            .all()
        )

        # Mit Benutzerinformationen anreichern
        enriched_messages = []

        for message in messages:
            message_dict = message.to_dict()

            # User laden (falls vorhanden)
            user = User.query.get(message.user_id) if message.user_id else None

            # User-Informationen hinzufügen
            if user:
                message_dict.update(
                    {
                        "username": user.username,
                        "user_exists": True,
                        "user_avatar": getattr(user, "avatar_url", None),
                        "is_admin": getattr(user, "is_admin", False),
                    }
                )
            else:
                message_dict.update(
                    {
                        "username": f"Gelöschter Benutzer (ID: {message.user_id})",
                        "user_exists": False,
                        "user_avatar": None,
                        "is_admin": False,
                    }
                )

            enriched_messages.append(message_dict)

        return enriched_messages

    except Exception as e:
        app.logger.error(f"❌ Fehler beim Laden der Nachrichten mit Users: {e}")
        return []


# ✅ NEU: Hilfsfunktion für User-Info
def get_user_info(user_id):
    """
    Holt Benutzerinformationen für eine User-ID
    """
    try:
        user = User.query.get(user_id)

        if user:
            return {
                "id": user.id,
                "username": user.username,
                "exists": True,
                "avatar_url": getattr(user, "avatar_url", None),
                "is_admin": getattr(user, "is_admin", False),
            }
        else:
            return {
                "id": user_id,
                "username": f"Gelöschter Benutzer (ID: {user_id})",
                "exists": False,
                "avatar_url": None,
                "is_admin": False,
            }
    except Exception as e:
        app.logger.error(f"❌ Fehler beim Laden der User-Info für ID {user_id}: {e}")
        return {
            "id": user_id,
            "username": f"Unbekannter Benutzer (ID: {user_id})",
            "exists": False,
            "avatar_url": None,
            "is_admin": False,
        }


# ✅ NEU: Bereinigungsfunktion für gelöschte User
def cleanup_user_data(user_id):
    """
    Bereinigt Chat-Daten eines gelöschten Users (optional)
    """
    try:
        app.logger.info(f"🧹 Bereinige Chat-Daten für User {user_id}...")

        # Option 1: Nachrichten löschen
        deleted_messages = BasicChatChatMessages.query.filter_by(
            user_id=user_id
        ).delete()
        app.logger.info(f"🗑️ {deleted_messages} Nachrichten gelöscht")

        # Option 2: User aus Gruppenmitgliedschaften entfernen
        group_chats = BasicChatGroupChat.query.all()
        for chat in group_chats:
            if chat.group_members and str(user_id) in chat.group_members:
                members = [
                    m
                    for m in chat.group_members.split(",")
                    if m.strip() != str(user_id)
                ]
                chat.group_members = ",".join(members) if members else ""

            if chat.group_admins and str(user_id) in chat.group_admins:
                admins = [
                    a for a in chat.group_admins.split(",") if a.strip() != str(user_id)
                ]
                chat.group_admins = ",".join(admins) if admins else ""

        # Option 3: Normale Chats löschen wo User beteiligt ist
        deleted_normal_chats = BasicChatNormalChat.query.filter(
            (BasicChatNormalChat.a_user_id == user_id)
            | (BasicChatNormalChat.b_user_id == user_id)
        ).delete()
        app.logger.info(f"🗑️ {deleted_normal_chats} normale Chats gelöscht")

        # Option 4: created_by_user_id auf NULL setzen
        group_chats = BasicChatGroupChat.query.filter_by(
            created_by_user_id=user_id
        ).all()
        for chat in group_chats:
            chat.created_by_user_id = None

        db.session.commit()
        app.logger.info(f"✅ Chat-Daten für User {user_id} erfolgreich bereinigt")
        return True

    except Exception as e:
        app.logger.error(
            f"❌ Fehler beim Bereinigen der Chat-Daten für User {user_id}: {e}"
        )
        db.session.rollback()
        return False


def delete_all_messages_from_room_simple(chat_room_number):
    """
    Löscht alle Nachrichten aus einem Chat-Raum anhand der room_number
    (Diese Funktion hatten wir schon - hier nochmal zur Vollständigkeit)
    """
    try:
        # Alle Nachrichten mit dieser chat_room_number finden und löschen
        deleted_count = BasicChatChatMessages.query.filter_by(
            chat_room_number=chat_room_number
        ).delete()

        # Änderungen speichern
        db.session.commit()

        app.logger.warning(
            f"🗑️ ADMIN-LÖSCHUNG: {deleted_count} Nachrichten aus Raum {chat_room_number} gelöscht"
        )

        return deleted_count

    except Exception as e:
        app.logger.error(f"❌ Fehler beim Löschen der Nachrichten: {e}")
        db.session.rollback()
        raise e


def get_all_group_chats_for_admin():
    """
    Holt alle Gruppenchats mit Details für Admin-Verwaltung
    """
    try:
        # Alle Gruppenchats laden
        all_group_chats = BasicChatGroupChat.query.order_by(
            BasicChatGroupChat.created_at.desc()
        ).all()

        group_chats_data = []

        for chat in all_group_chats:
            # Zusätzliche Statistiken berechnen
            message_count = BasicChatChatMessages.query.filter_by(
                group_chat_id=chat.id
            ).count()

            # Creator-Info laden
            creator_username = "Unbekannt"
            if chat.created_by_user_id:
                creator = get_user_info(chat.created_by_user_id)
                creator_username = creator["username"]

            # Member-Count berechnen
            member_count = 0
            if chat.group_members and chat.group_members != "*":
                member_ids = [
                    id.strip()
                    for id in chat.group_members.split(",")
                    if id.strip().isdigit()
                ]
                member_count = len(member_ids)
            elif chat.group_members == "*":
                member_count = "Alle User"

            # Chat-Daten zusammenstellen
            chat_data = {
                "id": chat.id,
                "chat_room_number": chat.chat_room_number,
                "group_name": chat.group_name,
                "group_admins": chat.group_admins,
                "group_members": chat.group_members,
                "group_avatar_url": chat.group_avatar_url,
                "created_at": chat.created_at.isoformat() if chat.created_at else None,
                "last_message_date": (
                    chat.last_message_date.isoformat()
                    if chat.last_message_date
                    else None
                ),
                "last_message": chat.last_message,
                "created_by_user_id": chat.created_by_user_id,
                # Zusätzliche Admin-Info
                "creator_username": creator_username,
                "member_count": member_count,
                "message_count": message_count,
            }

            group_chats_data.append(chat_data)

        app.logger.info(
            f"📊 Admin-Anfrage: {len(group_chats_data)} Gruppenchats geladen"
        )
        return group_chats_data

    except Exception as e:
        app.logger.error(f"❌ Fehler beim Laden der Gruppenchats für Admin: {e}")
        return []
