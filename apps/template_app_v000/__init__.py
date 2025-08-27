from flask import Blueprint

blueprint = Blueprint(
    "Template_app_v000",
    __name__,
    url_prefix="/Template_app_v000",
    template_folder="templates",
    static_folder="static",
    static_url_path="/Template_app_v000_static",
)
