from datetime import datetime
from pytz import timezone
from app import db

def get_current_time():
    return datetime.now(tz=timezone('Europe/Zurich')).replace(second=0, microsecond=0)


class CliCommandHistory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    command_run_at = db.Column(db.DateTime, index=True, default=get_current_time)
    user = db.Column(db.String(255))
    command = db.Column(db.String(255))
