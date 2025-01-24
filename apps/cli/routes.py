from flask import render_template, current_app as app, request, jsonify
from flask_login import current_user
from . import blueprint
from app.config import Config
from app.decorators import admin_required
from .models import CliCommandHistory
from app import db
import subprocess
import uuid
import threading
import queue
import sys

config = Config()

# Dictionary to store running commands
running_commands = {}

print("CLI Version 0.0.5")


def run_command(command_id, command):
    process = subprocess.Popen(
        command,
        shell=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
        errors="replace",
    )

    output_queue = queue.Queue()
    error_queue = queue.Queue()

    def enqueue_output(out, queue):
        for line in iter(out.readline, ""):
            queue.put(line)
        out.close()

    t1 = threading.Thread(target=enqueue_output, args=(process.stdout, output_queue))
    t2 = threading.Thread(target=enqueue_output, args=(process.stderr, error_queue))
    t1.daemon = True
    t2.daemon = True
    t1.start()
    t2.start()

    running_commands[command_id] = {
        "process": process,
        "output_queue": output_queue,
        "error_queue": error_queue,
        "complete": False,
    }


@blueprint.route("/cli_index", methods=["GET"])
@admin_required
def cli_index():
    app.logger.info("CLI page accessed")
    return render_template("cli.html", user=current_user, config=config)


@blueprint.route("/receive_command", methods=["POST"])
@admin_required
def receive_command():
    command = request.json.get("command")
    app.logger.info(f"{current_user.username} --> Command: {command}")

    # command_id = str(uuid.uuid4())

    new_command = CliCommandHistory(user=current_user.username, command=command)
    db.session.add(new_command)
    db.session.commit()
    threading.Thread(target=run_command, args=(new_command.id, command)).start()

    return jsonify({"command_id": new_command.id})


@blueprint.route("/check_output/<int:command_id>", methods=["GET"])
@admin_required
def check_output(command_id):
    print(f"Checking output for command_id: {command_id}")
    if command_id not in running_commands:
        print(f"Command {command_id} not found in running_commands")
        return jsonify({"error": "Command not found"}), 404

    command_info = running_commands[command_id]
    output = []
    error = []

    try:
        while not command_info["output_queue"].empty():
            output.append(command_info["output_queue"].get_nowait())
        while not command_info["error_queue"].empty():
            error.append(command_info["error_queue"].get_nowait())
    except Exception as e:
        app.logger.error(f"Error reading from queue: {str(e)}")

    if command_info["process"].poll() is not None:
        command_info["complete"] = True
        del running_commands[command_id]

    return jsonify(
        {"output": output, "error": error, "complete": command_info["complete"]}
    )


# not in use yet
@blueprint.route("/command_history", methods=["GET"])
@admin_required
def command_history():
    history = (
        CliCommandHistory.query.order_by(CliCommandHistory.command_run_at.desc())
        .limit(50)
        .all()
    )
    history_list = [
        {
            "user": cmd.user,
            "command": cmd.command,
            "run_at": cmd.command_run_at.strftime("%Y-%m-%d %H:%M:%S"),
        }
        for cmd in history
    ]
    return jsonify(history_list)


# not in use yet
@blueprint.route("/kill_command/<command_id>", methods=["POST"])
@admin_required
def kill_command(command_id):
    if command_id not in running_commands:
        return jsonify({"error": "Command not found"}), 404

    command_info = running_commands[command_id]
    try:
        command_info["process"].kill()
        del running_commands[command_id]
        return jsonify({"message": "Command terminated successfully"}), 200
    except Exception as e:
        app.logger.error(f"Error terminating command: {str(e)}")
        return jsonify({"error": "Failed to terminate command"}), 500
