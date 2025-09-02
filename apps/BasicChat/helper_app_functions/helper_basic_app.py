import os
import json
from ..models import BasicChatGroupChat, BasicChatNormalChat
import secrets, string
from app import db, app


# Variabeln
root_path = os.getcwd()
config_file_path = os.path.join(
    root_path, "app", "imported_apps", "develop_release", "BasicChat", "app_config.json"
)


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
