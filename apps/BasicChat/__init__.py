from flask import Blueprint

blueprint = Blueprint(
    "BasicChat",
    __name__,
    url_prefix="/BasicChat",
    template_folder="templates",
    static_folder="static",
    static_url_path="/BasicChat_static",
)
