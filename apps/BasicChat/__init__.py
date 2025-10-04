from flask import Blueprint
from app.logger_manager import AppLogger

blueprint = Blueprint(
    "BasicChat",
    __name__,
    url_prefix="/BasicChat",
    template_folder="templates",
    static_folder="static",
    static_url_path="/BasicChat_static",
)

app_logger = AppLogger("APP-BASICCHAT")
app_logger.info("Starte App-BasicChat Route Initialization")
