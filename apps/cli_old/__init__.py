from flask import Blueprint

blueprint = Blueprint(
    "PrintHub",
    __name__,
    url_prefix="/PrintHub",
    template_folder="templates",
    static_folder="static",
)

from . import routes
