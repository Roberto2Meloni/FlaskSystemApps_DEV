from datetime import datetime
from pytz import timezone
from app import db
from sqlalchemy import event


def get_current_time():
    return datetime.now(tz=timezone("Europe/Zurich")).replace(second=0, microsecond=0)


class BasicChatGroupChat(db.Model):
    __tablename__ = "basicchat_group_chat"

    first_default_message = "Chat erstellt"

    id = db.Column(db.Integer, primary_key=True)
    chat_room_number = db.Column(db.String(64), index=True, unique=True)
    group_name = db.Column(db.String(64), index=True)
    group_admins = db.Column(db.Text)  # LEGACY - wird bereinigt
    group_members = db.Column(db.Text)  # LEGACY - wird bereinigt
    group_avatar_url = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, index=True, default=get_current_time)
    last_message_date = db.Column(db.DateTime, index=True, default=get_current_time)
    last_message = db.Column(db.Text, default=first_default_message)
    created_by_user_id = db.Column(db.Integer, nullable=True, index=True)

    def to_dict(self):
        return {
            "id": self.id,
            "chat_room_number": self.chat_room_number,
            "group_name": self.group_name,
            "group_admins": self.group_admins,
            "group_members": self.group_members,
            "group_avatar_url": self.group_avatar_url,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "last_message_date": (
                self.last_message_date.isoformat() if self.last_message_date else None
            ),
            "last_message": self.last_message,
            "created_by_user_id": self.created_by_user_id,
        }


class BasicChatNormalChat(db.Model):
    __tablename__ = "basicchat_normal_chat"

    id = db.Column(db.Integer, primary_key=True)
    chat_room_number = db.Column(db.String(64), index=True, unique=True)
    last_message_date = db.Column(db.DateTime, index=True, default=get_current_time)
    last_message = db.Column(db.Text)
    created_at = db.Column(db.DateTime, index=True, default=get_current_time)
    a_user_id = db.Column(db.Integer, nullable=False, index=True)
    b_user_id = db.Column(db.Integer, nullable=False, index=True)

    def to_dict(self):
        return {
            "id": self.id,
            "chat_room_number": self.chat_room_number,
            "last_message_date": (
                self.last_message_date.isoformat() if self.last_message_date else None
            ),
            "last_message": self.last_message,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "a_user_id": self.a_user_id,
            "b_user_id": self.b_user_id,
        }


class BasicChatGroupMembership(db.Model):
    __tablename__ = "basicchat_group_membership"

    id = db.Column(db.Integer, primary_key=True)
    group_chat_id = db.Column(db.Integer, nullable=False, index=True)
    user_id = db.Column(db.Integer, nullable=False, index=True)
    is_admin = db.Column(db.Boolean, default=False)
    is_moderator = db.Column(db.Boolean, default=False)

    __table_args__ = (
        db.UniqueConstraint("group_chat_id", "user_id", name="unique_group_membership"),
    )


class BasicChatChatMessages(db.Model):
    __tablename__ = "basicchat_chat_messages"

    id = db.Column(db.Integer, primary_key=True)
    message = db.Column(db.Text)
    created_at = db.Column(db.DateTime, index=True, default=get_current_time)
    chat_room_number = db.Column(db.String(64), index=True, nullable=True)
    chat_type = db.Column(db.String(32), index=True, nullable=False)
    user_id = db.Column(db.Integer, nullable=False, index=True)
    group_chat_id = db.Column(db.Integer, nullable=True, index=True)
    normal_chat_id = db.Column(db.Integer, nullable=True, index=True)

    def to_dict(self):
        return {
            "id": self.id,
            "message": self.message,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "chat_room_number": self.chat_room_number,
            "chat_type": self.chat_type,
            "user_id": self.user_id,
        }

    def get_username(self):
        """Hilfsfunktion um den Username zu holen"""
        try:
            from app.routes.admin.models import User

            user = User.query.get(self.user_id)
            return (
                user.username if user else f"Gelöschter Benutzer (ID: {self.user_id})"
            )
        except:
            return f"Unbekannter Benutzer (ID: {self.user_id})"


# ==================== EVENT LISTENER FÜR MIGRATION ====================


def migrate_members_to_membership_table(mapper, connection, target):
    """
    Event Listener: Migriert Member/Admin-Daten aus Text-Feldern
    in die BasicChatGroupMembership Tabelle und bereinigt die alten Felder
    """
    try:
        # Prüfen ob überhaupt Legacy-Daten vorhanden sind
        if not target.group_members and not target.group_admins:
            return

        # User IDs aus den komma-getrennten Strings extrahieren
        admin_ids = set()
        member_ids = set()

        if target.group_admins:
            admin_ids = {
                int(uid.strip())
                for uid in target.group_admins.split(",")
                if uid.strip().isdigit()
            }

        if target.group_members:
            member_ids = {
                int(uid.strip())
                for uid in target.group_members.split(",")
                if uid.strip().isdigit()
            }

        # Alle User IDs kombinieren (Admins sind auch Members)
        all_user_ids = admin_ids.union(member_ids)

        # Membership-Einträge erstellen
        for user_id in all_user_ids:
            # Prüfen ob bereits vorhanden
            existing = connection.execute(
                db.text(
                    "SELECT id FROM basicchat_group_membership "
                    "WHERE group_chat_id = :group_id AND user_id = :user_id"
                ),
                {"group_id": target.id, "user_id": user_id},
            ).fetchone()

            if not existing:
                # Neuen Eintrag erstellen
                is_admin = user_id in admin_ids
                connection.execute(
                    db.text(
                        "INSERT INTO basicchat_group_membership "
                        "(group_chat_id, user_id, is_admin, is_moderator) "
                        "VALUES (:group_id, :user_id, :is_admin, :is_moderator)"
                    ),
                    {
                        "group_id": target.id,
                        "user_id": user_id,
                        "is_admin": is_admin,
                        "is_moderator": False,
                    },
                )

        # Legacy-Felder leeren
        connection.execute(
            db.text(
                "UPDATE basicchat_group_chat "
                "SET group_admins = NULL, group_members = NULL "
                "WHERE id = :group_id"
            ),
            {"group_id": target.id},
        )

        print(
            f"✅ Migration abgeschlossen für Gruppenchat ID {target.id}: "
            f"{len(all_user_ids)} Members migriert ({len(admin_ids)} Admins)"
        )

    except Exception as e:
        print(f"❌ Fehler bei Member-Migration für Gruppenchat ID {target.id}: {e}")


# Event Listener registrieren
event.listens_for(BasicChatGroupChat, "after_insert")(
    migrate_members_to_membership_table
)
event.listens_for(BasicChatGroupChat, "after_update")(
    migrate_members_to_membership_table
)


# ==================== HILFSFUNKTIONEN ====================


def get_user_by_id(user_id):
    """Hilfsfunktion um einen User zu holen"""
    try:
        from app.routes.admin.models import User

        return User.query.get(user_id)
    except:
        return None


def get_username_by_id(user_id):
    """Hilfsfunktion um einen Username zu holen"""
    user = get_user_by_id(user_id)
    return user.username if user else f"Gelöschter Benutzer (ID: {user_id})"


def cleanup_deleted_user_data(user_id):
    """Hilfsfunktion um Chat-Daten eines gelöschten Users zu bereinigen"""
    try:
        # Nachrichten löschen
        BasicChatChatMessages.query.filter_by(user_id=user_id).delete()

        # User aus Gruppenmitgliedschaften entfernen
        BasicChatGroupMembership.query.filter_by(user_id=user_id).delete()

        # Normale Chats löschen
        BasicChatNormalChat.query.filter(
            (BasicChatNormalChat.a_user_id == user_id)
            | (BasicChatNormalChat.b_user_id == user_id)
        ).delete()

        # created_by_user_id auf NULL setzen
        group_chats = BasicChatGroupChat.query.filter_by(
            created_by_user_id=user_id
        ).all()
        for chat in group_chats:
            chat.created_by_user_id = None

        db.session.commit()
        return True
    except Exception as e:
        db.session.rollback()
        print(f"Fehler beim Bereinigen der Chat-Daten für User {user_id}: {e}")
        return False


def migrate_all_legacy_groups():
    """
    Manuelle Migration für alle bestehenden Legacy-Gruppen
    Kann einmalig aufgerufen werden, um alle alten Daten zu migrieren
    """
    try:
        legacy_groups = BasicChatGroupChat.query.filter(
            (BasicChatGroupChat.group_admins.isnot(None))
            | (BasicChatGroupChat.group_members.isnot(None))
        ).all()

        migrated_count = 0
        for group in legacy_groups:
            # Trigger die Migration durch ein Update
            db.session.add(group)
            db.session.flush()
            migrated_count += 1

        db.session.commit()
        print(f"✅ {migrated_count} Legacy-Gruppen erfolgreich migriert")
        return True

    except Exception as e:
        db.session.rollback()
        print(f"❌ Fehler bei der Legacy-Migration: {e}")
        return False
