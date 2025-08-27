from flask import Blueprint

blueprint = Blueprint(
    "Cli",
    __name__,
    url_prefix="/Cli",
    template_folder="templates",
    static_folder="static",
    static_url_path="/Cli_static",
)
