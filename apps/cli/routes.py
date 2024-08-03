from flask import render_template, current_app as app, request, jsonify
from flask_login import current_user
from . import blueprint
from app.config import Config
from app.decorators import admin_required
from app.config import Config
from jinja2 import Environment, FileSystemLoader
import os
import subprocess

config = Config()
root_paht = os.getcwd()
this_app_path = os.path.join(root_paht, 'app', 'imported_apps', 'develop_release', 'cli' )

# template_dir = os.path.join(this_app_path, 'templates')
# env = Environment(loader=FileSystemLoader(template_dir))

@blueprint.route('/', methods=['POST', 'GET'])
def cli():
    app.logger.info("CLI Testseite angesurft")
    print("CLI angesurft")

    if request.method == 'POST':
        print("Post erhalten")
        command = request.json.get('command')
        print(f"Kommando: {command}")
        
        try:
            result = subprocess.run(command, shell=True, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            response = {
                'output': result.stdout.decode('utf-8').split('\n'),
                'error': result.stderr.decode('utf-8').split('\n'),
                'returncode': result.returncode
            }
        except subprocess.CalledProcessError as e:
            response = {
                'output': e.stdout.decode('utf-8').split('\n') if e.stdout else '',
                'error': e.stderr.decode('utf-8').split('\n') if e.stderr else ['Fehler beim Ausführen des Kommandos'],
                'returncode': e.returncode
            }

        return jsonify(response)

    return render_template("cli.html", user=current_user, config=config)
