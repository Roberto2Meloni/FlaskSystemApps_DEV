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
    created_by_user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)

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
    __tablename__ = "basicchat_normal_chat"  # ← HIER WAR DER FEHLER!

    id = db.Column(db.Integer, primary_key=True)
    chat_room_number = db.Column(db.String(64), index=True, unique=True)
    last_message_date = db.Column(db.DateTime, index=True, default=get_current_time)
    last_message = db.Column(db.Text)
    created_at = db.Column(db.DateTime, index=True, default=get_current_time)
    a_user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    b_user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)

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
    group_chat_id = db.Column(
        db.Integer, db.ForeignKey("basicchat_group_chat.id"), nullable=False
    )
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)

    # Rollen
    is_admin = db.Column(db.Boolean, default=False)
    is_moderator = db.Column(db.Boolean, default=False)

    # Unique constraint
    __table_args__ = (
        db.UniqueConstraint("group_chat_id", "user_id", name="unique_group_membership"),
    )


class BasicChatChatMessages(db.Model):
    __tablename__ = "basicchat_chat_messages"

    id = db.Column(db.Integer, primary_key=True)
    message = db.Column(db.Text)
    created_at = db.Column(db.DateTime, index=True, default=get_current_time)

    # NEU: Direkte room_number Referenz
    chat_room_number = db.Column(
        db.String(64), index=True, nullable=True
    )  # Erst nullable für Migration

    # Chat-Zuordnung (behalten für Backward-Compatibility)
    chat_type = db.Column(db.String(32), index=True, nullable=False)
    group_chat_id = db.Column(
        db.Integer, db.ForeignKey("basicchat_group_chat.id"), nullable=True
    )
    normal_chat_id = db.Column(
        db.Integer, db.ForeignKey("basicchat_normal_chat.id"), nullable=True
    )
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)

    def to_dict(self):
        return {
            "id": self.id,
            "message": self.message,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "chat_room_number": self.chat_room_number,
            "chat_type": self.chat_type,
            "user_id": self.user_id,
        }
