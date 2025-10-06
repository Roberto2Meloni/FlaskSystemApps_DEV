import os
import json
from ..models import (
    BasicChatGroupChat,
    BasicChatNormalChat,
    BasicChatChatMessages,
    BasicChatGroupMembership,
)
import secrets, string
from app import db, app
from sqlalchemy import or_
from datetime import datetime
from pytz import timezone


# ✅ NEU: User Model Import für Benutzerinformationen
from app.routes.admin.models import User
from .. import app_logger


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


def creat_group_chat_number(existing_group_chat_numbers):
    while True:
        new_number = "".join(
            secrets.choice(string.ascii_letters + string.digits) for _ in range(16)
        )
        if new_number not in existing_group_chat_numbers:
            return new_number


def create_new_group_chat(group_name, current_user):
    """Erstellt einen neuen Gruppenchat mit korrekter Membership"""
    try:
        all_numbers = get_all_chat_room_numbers()
        new_chat_number = creat_group_chat_number(all_numbers)

        # ✅ KORRIGIERT: Legacy-Felder auf None/leer setzen
        new_group_chat = BasicChatGroupChat(
            chat_room_number=new_chat_number,
            group_name=group_name,
            group_admins=None,  # ← Legacy, nicht mehr verwendet
            group_members=None,  # ← Legacy, nicht mehr verwendet
            created_by_user_id=current_user.id,
        )
        db.session.add(new_group_chat)
        db.session.flush()  # ← ID erhalten ohne zu committen

        # ✅ Membership für Ersteller erstellen
        creator_membership = BasicChatGroupMembership(
            group_chat_id=new_group_chat.id,
            user_id=current_user.id,
            is_admin=True,
            is_moderator=False,
        )
        db.session.add(creator_membership)
        db.session.commit()

        print(f"✅ Gruppenchat '{group_name}' erstellt (ID: {new_group_chat.id})")
        return new_group_chat

    except Exception as e:
        db.session.rollback()
        print(f"❌ Fehler beim Erstellen des Gruppenchats: {e}")
        raise


def create_global_group_chat():
    """Erstellt globalen Chat mit korrekter Membership"""
    try:
        app_logger.debug("🔍 Prüfe ob globaler Chat existiert...")

        with db.session.no_autoflush:
            existing_global_chat = BasicChatGroupChat.query.filter_by(
                group_name="Global"
            ).first()

        if not existing_global_chat:
            app_logger.warning("➕ Globaler Chat existiert nicht! Erstelle...")

            all_numbers = get_all_chat_room_numbers()
            new_number = creat_group_chat_number(all_numbers)

            # ✅ KORRIGIERT: Globalen Chat erstellen
            new_global_group_chat = BasicChatGroupChat(
                chat_room_number=new_number,
                group_name="Global",
                group_admins=None,  # ← Legacy
                group_members="*",  # ← Legacy: Marker für "öffentlich"
                created_by_user_id=1,
            )
            db.session.add(new_global_group_chat)
            db.session.flush()  # ← ID erhalten

            # ✅ Admin-Membership erstellen
            admin_membership = BasicChatGroupMembership(
                group_chat_id=new_global_group_chat.id,
                user_id=1,  # Admin
                is_admin=True,
                is_moderator=False,
            )
            db.session.add(admin_membership)
            db.session.commit()

            app_logger.info("✅ Globaler Chat erfolgreich erstellt!")
        else:
            app_logger.info("ℹ️ Globaler Chat existiert bereits")

    except Exception as e:
        app_logger.error(f"❌ Fehler beim Erstellen des globalen Chats: {e}")
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
        app_logger.critical(
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

            app_logger.debug("✅ Fallback globaler Chat erstellt")

        except Exception as fallback_error:
            app_logger.error(f"❌ Auch Fallback fehlgeschlagen: {fallback_error}")
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
        app_logger.error(f"❌ Fehler beim Abrufen der globalen Chat-ID: {e}")
        return None


def get_all_my_chats(current_user):
    """
    ✅ AKTUALISIERT: Holt alle Chats über Membership-Tabelle
    """
    try:
        # 1. Group Chats über Membership-Tabelle
        user_memberships = BasicChatGroupMembership.query.filter_by(
            user_id=current_user.id
        ).all()
        membership_chat_ids = [m.group_chat_id for m in user_memberships]

        # 2. FALLBACK: Alte Text-Felder (für Legacy-Daten)
        legacy_chats = BasicChatGroupChat.query.filter(
            or_(
                BasicChatGroupChat.group_members == "*",  # Öffentlich
                BasicChatGroupChat.group_admins.contains(str(current_user.id)),
                BasicChatGroupChat.group_members.contains(str(current_user.id)),
            )
        ).all()
        legacy_chat_ids = [chat.id for chat in legacy_chats]

        # 3. Kombinieren (unique IDs)
        all_group_chat_ids = list(set(membership_chat_ids + legacy_chat_ids))

        # Group Chats laden
        group_chats = (
            BasicChatGroupChat.query.filter(
                BasicChatGroupChat.id.in_(all_group_chat_ids)
            ).all()
            if all_group_chat_ids
            else []
        )

        # Normal Chats laden
        normal_chats = BasicChatNormalChat.query.filter(
            or_(
                BasicChatNormalChat.a_user_id == current_user.id,
                BasicChatNormalChat.b_user_id == current_user.id,
            )
        ).all()

        return group_chats + normal_chats

    except Exception as e:
        app_logger.error(f"❌ Fehler beim Laden der Chats: {e}")
        return []


def get_all_my_chats_with_users(current_user):
    """
    ✅ AKTUALISIERT: Holt alle Chats MIT User-Info über Membership-Tabelle
    """
    try:
        all_chats = []

        # 1. Group Chats über Membership-Tabelle
        user_memberships = BasicChatGroupMembership.query.filter_by(
            user_id=current_user.id
        ).all()
        membership_chat_ids = [m.group_chat_id for m in user_memberships]

        # 2. FALLBACK: Legacy-Daten
        legacy_chats = BasicChatGroupChat.query.filter(
            or_(
                BasicChatGroupChat.group_members == "*",
                BasicChatGroupChat.group_admins.contains(str(current_user.id)),
                BasicChatGroupChat.group_members.contains(str(current_user.id)),
            )
        ).all()
        legacy_chat_ids = [chat.id for chat in legacy_chats]

        # 3. Kombinieren
        all_group_chat_ids = list(set(membership_chat_ids + legacy_chat_ids))

        # Group Chats laden
        group_chats = (
            BasicChatGroupChat.query.filter(
                BasicChatGroupChat.id.in_(all_group_chat_ids)
            ).all()
            if all_group_chat_ids
            else []
        )

        # Für jeden Group Chat: User-Info aus Membership laden
        for chat in group_chats:
            chat_dict = chat.to_dict()
            chat_dict["type"] = "group"

            # Creator-Info
            if chat.created_by_user_id:
                creator = User.query.get(chat.created_by_user_id)
                chat_dict["creator_username"] = (
                    creator.username
                    if creator
                    else f"Gelöschter User (ID: {chat.created_by_user_id})"
                )

            # Members aus Membership-Tabelle
            memberships = BasicChatGroupMembership.query.filter_by(
                group_chat_id=chat.id
            ).all()

            member_ids = [m.user_id for m in memberships]
            admin_ids = [m.user_id for m in memberships if m.is_admin]

            if member_ids:
                members = User.query.filter(User.id.in_(member_ids)).all()
                chat_dict["members_with_names"] = [
                    {
                        "id": user.id,
                        "username": user.username,
                        "is_admin": user.id in admin_ids,
                    }
                    for user in members
                ]
            else:
                chat_dict["members_with_names"] = []

            # Admin-Liste
            if admin_ids:
                admins = User.query.filter(User.id.in_(admin_ids)).all()
                chat_dict["admins_with_names"] = [
                    {"id": user.id, "username": user.username} for user in admins
                ]
            else:
                chat_dict["admins_with_names"] = []

            all_chats.append(chat_dict)

        # Normal Chats
        normal_chats = BasicChatNormalChat.query.filter(
            or_(
                BasicChatNormalChat.a_user_id == current_user.id,
                BasicChatNormalChat.b_user_id == current_user.id,
            )
        ).all()

        for chat in normal_chats:
            chat_dict = chat.to_dict()
            chat_dict["type"] = "normal"

            other_user_id = (
                chat.b_user_id if chat.a_user_id == current_user.id else chat.a_user_id
            )
            other_user = User.query.get(other_user_id)

            chat_dict["other_user_id"] = other_user_id
            chat_dict["other_username"] = (
                other_user.username
                if other_user
                else f"Gelöschter User (ID: {other_user_id})"
            )
            chat_dict["display_name"] = chat_dict["other_username"]

            all_chats.append(chat_dict)

        return all_chats

    except Exception as e:
        app_logger.error(f"❌ Fehler beim Laden der Chats mit Users: {e}")
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


def find_chat_by_room_number_with_users(chat_room_number, current_user):
    """
    Findet einen Chat MIT Benutzerinformationen und prüft Berechtigung
    Verwendet die neue BasicChatGroupMembership Tabelle
    Rückgabe: chat_dict, chat_type, error_message
    """
    try:
        # ========== GROUP CHATS ==========
        group_chat = BasicChatGroupChat.query.filter_by(
            chat_room_number=chat_room_number
        ).first()

        if group_chat:
            # Berechtigung über Membership-Tabelle prüfen
            is_member = BasicChatGroupMembership.query.filter_by(
                group_chat_id=group_chat.id, user_id=current_user.id
            ).first()

            # FALLBACK für Legacy-Daten (falls noch nicht migriert)
            legacy_has_access = False
            if group_chat.group_members == "*":
                legacy_has_access = True
            elif group_chat.group_members or group_chat.group_admins:
                legacy_has_access = str(current_user.id) in (
                    group_chat.group_admins or ""
                ) or str(current_user.id) in (group_chat.group_members or "")

            # Zugriff gewähren wenn Member ODER Legacy-Zugriff
            if is_member or legacy_has_access:
                chat_dict = group_chat.to_dict()

                # Creator-Info hinzufügen
                if group_chat.created_by_user_id:
                    creator = User.query.get(group_chat.created_by_user_id)
                    chat_dict["creator_username"] = (
                        creator.username
                        if creator
                        else f"Gelöschter User (ID: {group_chat.created_by_user_id})"
                    )

                # Members aus Membership-Tabelle laden
                memberships = BasicChatGroupMembership.query.filter_by(
                    group_chat_id=group_chat.id
                ).all()

                # Alle User IDs der Members sammeln
                member_ids = [m.user_id for m in memberships]
                admin_ids = [m.user_id for m in memberships if m.is_admin]

                # Members mit Namen laden
                if member_ids:
                    members = User.query.filter(User.id.in_(member_ids)).all()
                    chat_dict["members_with_names"] = [
                        {
                            "id": user.id,
                            "username": user.username,
                            "is_admin": user.id in admin_ids,
                        }
                        for user in members
                    ]
                else:
                    chat_dict["members_with_names"] = []

                # Admins mit Namen (nur Admins)
                if admin_ids:
                    admins = User.query.filter(User.id.in_(admin_ids)).all()
                    chat_dict["admins_with_names"] = [
                        {"id": user.id, "username": user.username} for user in admins
                    ]
                else:
                    chat_dict["admins_with_names"] = []

                # Ist aktueller User Admin?
                chat_dict["current_user_is_admin"] = (
                    is_member.is_admin if is_member else False
                )

                return chat_dict, "group", ""
            else:
                return None, None, "Keine Berechtigung für diesen Gruppenchat"

        # ========== NORMAL CHATS ==========
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

                # Display-Name für aktuellen User (Chat-Partner)
                if current_user.id == normal_chat.a_user_id:
                    chat_dict["display_name"] = chat_dict["user_b_username"]
                    chat_dict["partner_id"] = normal_chat.b_user_id
                else:
                    chat_dict["display_name"] = chat_dict["user_a_username"]
                    chat_dict["partner_id"] = normal_chat.a_user_id

                return chat_dict, "normal", ""
            else:
                return None, None, "Keine Berechtigung für diesen Chat"

        return None, None, "Chat nicht gefunden"

    except Exception as e:
        from flask import current_app as app

        app_logger.error(f"❌ Fehler beim Suchen des Chats mit Users: {e}")
        import traceback

        app_logger.error(traceback.format_exc())
        return None, None, "Serverfehler beim Laden des Chats"


# ========== ZUSÄTZLICHE HILFSFUNKTION ==========


def check_user_chat_permission(chat_room_number, user_id):
    """
    Schnelle Berechtigungsprüfung ohne User-Details zu laden
    Gibt True/False zurück
    """
    try:
        # Group Chat prüfen
        group_chat = BasicChatGroupChat.query.filter_by(
            chat_room_number=chat_room_number
        ).first()

        if group_chat:
            # Membership prüfen
            is_member = BasicChatGroupMembership.query.filter_by(
                group_chat_id=group_chat.id, user_id=user_id
            ).first()

            if is_member:
                return True

            # Legacy Fallback
            if group_chat.group_members == "*":
                return True
            if str(user_id) in (group_chat.group_admins or "") or str(user_id) in (
                group_chat.group_members or ""
            ):
                return True

            return False

        # Normal Chat prüfen
        normal_chat = BasicChatNormalChat.query.filter_by(
            chat_room_number=chat_room_number
        ).first()

        if normal_chat:
            return user_id == normal_chat.a_user_id or user_id == normal_chat.b_user_id

        return False

    except Exception as e:
        from flask import current_app as app

        app_logger.error(f"❌ Fehler bei Berechtigungsprüfung: {e}")
        return False


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
        app_logger.error(f"❌ Fehler beim Speichern der Nachricht mit User-Info: {e}")
        db.session.rollback()
        return None


def get_all_messages_from_chat_room_with_users(chat_room_number):
    """
    Lädt alle Nachrichten eines Chats MIT Benutzerinformationen
    Verwendet keine Relationships mehr, sondern manuelle User-Lookups
    """
    try:
        # Nachrichten aus DB laden
        messages = (
            BasicChatChatMessages.query.filter_by(chat_room_number=chat_room_number)
            .order_by(BasicChatChatMessages.created_at.asc())
            .all()
        )

        if not messages:
            return []

        # Alle User IDs sammeln (unique)
        user_ids = list(set(msg.user_id for msg in messages))

        # Alle User auf einmal laden (Performance!)
        users = User.query.filter(User.id.in_(user_ids)).all()
        user_dict = {user.id: user for user in users}

        # Wenn es ein Group Chat ist, Admin-Status laden
        admin_status_dict = {}
        if messages and messages[0].chat_type == "group" and messages[0].group_chat_id:
            memberships = BasicChatGroupMembership.query.filter_by(
                group_chat_id=messages[0].group_chat_id
            ).all()
            admin_status_dict = {m.user_id: m.is_admin for m in memberships}

        # Nachrichten mit User-Info zusammenbauen
        messages_with_users = []
        for msg in messages:
            message_dict = msg.to_dict()

            # User-Info hinzufügen
            user = user_dict.get(msg.user_id)
            if user:
                message_dict["username"] = user.username
                message_dict["user_avatar"] = getattr(user, "avatar_url", None)
            else:
                message_dict["username"] = f"Gelöschter User (ID: {msg.user_id})"
                message_dict["user_avatar"] = None

            # Admin-Status hinzufügen (nur bei Group Chats)
            if msg.chat_type == "group":
                message_dict["is_admin"] = admin_status_dict.get(msg.user_id, False)
            else:
                message_dict["is_admin"] = False

            messages_with_users.append(message_dict)

        return messages_with_users

    except Exception as e:
        from flask import current_app as app

        app_logger.error(f"❌ Fehler beim Laden der Nachrichten mit Users: {e}")
        import traceback

        app_logger.error(traceback.format_exc())
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
        app_logger.error(f"❌ Fehler beim Laden der User-Info für ID {user_id}: {e}")
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
        app_logger.info(f"🧹 Bereinige Chat-Daten für User {user_id}...")

        # Option 1: Nachrichten löschen
        deleted_messages = BasicChatChatMessages.query.filter_by(
            user_id=user_id
        ).delete()
        app_logger.info(f"🗑️ {deleted_messages} Nachrichten gelöscht")

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
        app_logger.info(f"🗑️ {deleted_normal_chats} normale Chats gelöscht")

        # Option 4: created_by_user_id auf NULL setzen
        group_chats = BasicChatGroupChat.query.filter_by(
            created_by_user_id=user_id
        ).all()
        for chat in group_chats:
            chat.created_by_user_id = None

        db.session.commit()
        app_logger.info(f"✅ Chat-Daten für User {user_id} erfolgreich bereinigt")
        return True

    except Exception as e:
        app_logger.error(
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

        app_logger.warning(
            f"🗑️ ADMIN-LÖSCHUNG: {deleted_count} Nachrichten aus Raum {chat_room_number} gelöscht"
        )

        return deleted_count

    except Exception as e:
        app_logger.error(f"❌ Fehler beim Löschen der Nachrichten: {e}")
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

        app_logger.info(
            f"📊 Admin-Anfrage: {len(group_chats_data)} Gruppenchats geladen"
        )
        return group_chats_data

    except Exception as e:
        app_logger.error(f"❌ Fehler beim Laden der Gruppenchats für Admin: {e}")
        return []


def get_all_chat_room_numbers():
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

    return all_numbers


def add_group_chat_member(group_chat_id, all_user_id):
    """
    ✅ KORRIGIERT: Sichere Integer-Konvertierung
    """
    error_message = None
    success = False
    added_users = []

    try:
        # Gruppe existiert?
        group_chat = BasicChatGroupChat.query.get(group_chat_id)
        if not group_chat:
            return False, [], "Gruppe nicht gefunden"

        # ✅ NEU: Konvertiere zu Integers
        all_user_id = [int(uid) for uid in all_user_id]

        # Bereits vorhandene Members
        existing_memberships = BasicChatGroupMembership.query.filter_by(
            group_chat_id=group_chat_id
        ).all()
        already_member_ids = [m.user_id for m in existing_memberships]

        # Nur neue User hinzufügen
        to_add_users = [uid for uid in all_user_id if uid not in already_member_ids]

        if not to_add_users:
            return False, [], "Alle Benutzer sind bereits Mitglied"

        # User als Member hinzufügen
        for user_id in to_add_users:
            # Prüfe ob User existiert
            user = User.query.get(user_id)
            if not user:
                print(f"⚠️ User {user_id} existiert nicht, überspringe...")
                continue

            new_member = BasicChatGroupMembership(
                group_chat_id=group_chat_id,
                user_id=user_id,  # ← Jetzt garantiert Integer
                is_admin=False,
                is_moderator=False,
            )
            db.session.add(new_member)
            added_users.append(user_id)  # ← Jetzt garantiert Integer

        db.session.commit()
        success = True
        print(f"✅ {len(added_users)} User zu Gruppe {group_chat_id} hinzugefügt")

    except Exception as e:
        db.session.rollback()
        error_message = f"Datenbankfehler: {str(e)}"
        print(f"❌ Fehler in add_group_chat_member: {e}")

    return success, added_users, error_message
