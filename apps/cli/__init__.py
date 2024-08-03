from flask import Blueprint

blueprint = Blueprint(
    'cli',
    __name__,
    url_prefix='/cli',
     template_folder='templates',
     static_folder='static',
)
