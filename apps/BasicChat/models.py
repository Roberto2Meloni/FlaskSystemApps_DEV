from datetime import datetime
from pytz import timezone
from app import db


def get_current_time():
    return datetime.now(tz=timezone("Europe/Zurich")).replace(second=0, microsecond=0)


class BasicChatGroupChat(db.Model):
    __tablename__ = "basicchat_group_chat"

    first_default_message = "Chat erstellt"

    id = db.Column(db.Integer, primary_key=True)
    chat_room_number = db.Column(db.String(64), index=True, unique=True)
    group_name = db.Column(db.String(64), index=True)
    group_admins = db.Column(db.Text)  # User ID's als Komma-getrennt
    group_members = db.Column(db.Text)  # User ID's als Komma-getrennt
    group_avatar_url = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, index=True, default=get_current_time)
    last_message_date = db.Column(db.DateTime, index=True, default=get_current_time)
    last_message = db.Column(db.Text, default=first_default_message)

    # ✅ GEÄNDERT: Kein Foreign Key, nur Integer ID
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

    # ✅ GEÄNDERT: Keine Foreign Keys, nur Integer IDs
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

    # ✅ GEÄNDERT: Kein Foreign Key für group_chat_id
    group_chat_id = db.Column(db.Integer, nullable=False, index=True)

    # ✅ GEÄNDERT: Kein Foreign Key für user_id
    user_id = db.Column(db.Integer, nullable=False, index=True)

    # Rollen
    is_admin = db.Column(db.Boolean, default=False)
    is_moderator = db.Column(db.Boolean, default=False)

    # ✅ GEÄNDERT: Unique constraint angepasst
    __table_args__ = (
        db.UniqueConstraint("group_chat_id", "user_id", name="unique_group_membership"),
    )


class BasicChatChatMessages(db.Model):
    __tablename__ = "basicchat_chat_messages"

    id = db.Column(db.Integer, primary_key=True)
    message = db.Column(db.Text)
    created_at = db.Column(db.DateTime, index=True, default=get_current_time)
    chat_room_number = db.Column(db.String(64), index=True, nullable=True)
    chat_type = db.Column(
        db.String(32), index=True, nullable=False
    )  # 'group' oder 'normal'

    # ✅ GEÄNDERT: Keine Foreign Keys, nur Integer IDs
    user_id = db.Column(db.Integer, nullable=False, index=True)
    group_chat_id = db.Column(db.Integer, nullable=True, index=True)
    normal_chat_id = db.Column(db.Integer, nullable=True, index=True)

    # ✅ ENTFERNT: Keine Relationship mehr
    # user = db.relationship("User", backref="chat_messages")

    def to_dict(self):
        # ✅ GEÄNDERT: Username wird separat geholt (falls benötigt)
        return {
            "id": self.id,
            "message": self.message,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "chat_room_number": self.chat_room_number,
            "chat_type": self.chat_type,
            "user_id": self.user_id,
            # Username muss jetzt separat über eine Hilfsfunktion geholt werden
        }

    def get_username(self):
        """
        Hilfsfunktion um den Username zu holen, falls User noch existiert
        """
        try:
            from app.routes.admin.models import (
                User,
            )  # Import hier, um Circular Imports zu vermeiden

            user = User.query.get(self.user_id)
            return (
                user.username if user else f"Gelöschter Benutzer (ID: {self.user_id})"
            )
        except:
            return f"Unbekannter Benutzer (ID: {self.user_id})"


# ✅ ZUSÄTZLICHE HILFSFUNKTIONEN für User-Lookup ohne Foreign Keys


def get_user_by_id(user_id):
    """
    Hilfsfunktion um einen User zu holen, falls er noch existiert
    """
    try:
        from app.routes.admin.models import User

        return User.query.get(user_id)
    except:
        return None


def get_username_by_id(user_id):
    """
    Hilfsfunktion um einen Username zu holen, falls User noch existiert
    """
    user = get_user_by_id(user_id)
    return user.username if user else f"Gelöschter Benutzer (ID: {user_id})"


def cleanup_deleted_user_data(user_id):
    """
    Hilfsfunktion um Chat-Daten eines gelöschten Users zu bereinigen
    Kann aufgerufen werden, bevor ein User gelöscht wird
    """
    try:
        # Option 1: Nachrichten löschen
        BasicChatChatMessages.query.filter_by(user_id=user_id).delete()

        # Option 2: User aus Gruppenmitgliedschaften entfernen
        BasicChatGroupMembership.query.filter_by(user_id=user_id).delete()

        # Option 3: Normale Chats löschen, wo User beteiligt ist
        BasicChatNormalChat.query.filter(
            (BasicChatNormalChat.a_user_id == user_id)
            | (BasicChatNormalChat.b_user_id == user_id)
        ).delete()

        # Option 4: created_by_user_id auf NULL setzen für Gruppenchats
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
