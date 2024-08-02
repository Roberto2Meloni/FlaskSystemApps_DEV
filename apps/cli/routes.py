# Import necessary modules
from app import app, db
from flask import render_template, url_for, flash, redirect, jsonify, get_flashed_messages
from flask_login import current_user
from app.routes.admin.models import User
from app.config import Config
from app.decorators import admin_required
from time import sleep


config = Config()

# Define a blueprint for authentication routes
from app.imported_apps.develop_release.cli import blueprint


@blueprint.route('/test', methods=['POST', 'GET'])
@admin_required
def test():
    new_registration = User.query.filter(User.user_enable.is_(None)).count()
    app.logger.info("dev tools Seite angesurf")
    return "dies ist die TEST CLI Seite"