import os
import json

# Variabeln
root_path = os.getcwd()
config_file_path = os.path.join(
    root_path, "app", "imported_apps", "develop_release", "BasicChat", "app_config.json"
)


def get_app_config():
    try:
        with open(config_file_path, "r", encoding="utf-8") as file:
            return json.load(file)
    except FileNotFoundError:
        return {}
