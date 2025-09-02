from datetime import datetime
from pytz import timezone
from app import db


def get_current_time():
    return datetime.now(tz=timezone("Europe/Zurich")).replace(second=0, microsecond=0)


class BasicChatGroupChat(db.Model):
    __tablename__ = "basicchat_group_chat"

    id = db.Column(db.Integer, primary_key=True)
    chat_room_number = db.Column(db.String(64), index=True, unique=True)
    group_name = db.Column(db.String(64), index=True)
    group_admins = db.Column(db.Text)  # User ID's als Komma-getrennt
    group_members = db.Column(db.Text)  # User ID's als Komma-getrennt
    group_avatar_url = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, index=True, default=get_current_time)
    last_message_date = db.Column(db.DateTime, index=True, default=get_current_time)
    last_message = db.Column(db.Text)
    created_by_user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)


class BasicChatNormalChat(db.Model):
    __tablename__ = "basicchat_normal_chat"  # ← HIER WAR DER FEHLER!

    id = db.Column(db.Integer, primary_key=True)
    chat_room_number = db.Column(db.String(64), index=True, unique=True)
    last_message_date = db.Column(db.DateTime, index=True, default=get_current_time)
    last_message = db.Column(db.Text)
    created_at = db.Column(db.DateTime, index=True, default=get_current_time)
    a_user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    b_user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)


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

    # Chat-Zuordnung
    chat_type = db.Column(
        db.String(32), index=True, nullable=False
    )  # 'group' oder 'normal'
    group_chat_id = db.Column(
        db.Integer, db.ForeignKey("basicchat_group_chat.id"), nullable=True
    )
    normal_chat_id = db.Column(
        db.Integer, db.ForeignKey("basicchat_normal_chat.id"), nullable=True
    )
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
