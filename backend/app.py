import os
import traceback

import anthropic
from dotenv import load_dotenv
from flask import Flask, jsonify, request
from flask_cors import CORS

from database import get_db_connection, init_db

load_dotenv()


app = Flask(__name__)
CORS(app)


def _fetch_all_tasks():
    # Read all tasks from the database and convert done to booleans.
    connection = get_db_connection()
    rows = connection.execute(
        "SELECT id, title, done, created_at FROM tasks ORDER BY id DESC"
    ).fetchall()
    connection.close()

    return [
        {
            "id": row["id"],
            "title": row["title"],
            "done": bool(row["done"]),
            "created_at": row["created_at"],
        }
        for row in rows
    ]


def _build_task_prompt(tasks):
    # Build a readable task list string to send to Claude.
    if not tasks:
        return "No tasks found."

    lines = []
    for task in tasks:
        status = "done" if task["done"] else "pending"
        lines.append(f'- [{status}] #{task["id"]}: {task["title"]}')
    return "\n".join(lines)


@app.route("/tasks", methods=["GET"])
def get_tasks():
    # Return all tasks sorted by newest first.
    try:
        tasks = _fetch_all_tasks()
        return jsonify(tasks), 200
    except Exception as e:
        print("FULL ERROR TRACEBACK in GET /tasks:")
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500


@app.route("/tasks", methods=["POST"])
def create_task():
    # Create a new task from JSON input.
    try:
        payload = request.get_json(silent=True) or {}
        title = (payload.get("title") or "").strip()

        if not title:
            return jsonify({"error": "Title is required"}), 400

        connection = get_db_connection()
        cursor = connection.execute("INSERT INTO tasks (title, done) VALUES (?, 0)", (title,))
        connection.commit()

        row = connection.execute(
            "SELECT id, title, done, created_at FROM tasks WHERE id = ?",
            (cursor.lastrowid,),
        ).fetchone()
        connection.close()

        task = {
            "id": row["id"],
            "title": row["title"],
            "done": bool(row["done"]),
            "created_at": row["created_at"],
        }
        return jsonify(task), 201
    except Exception as e:
        print("FULL ERROR TRACEBACK in POST /tasks:")
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500


@app.route("/tasks/<int:task_id>", methods=["PUT"])
def toggle_task(task_id):
    # Toggle a task between done and not done.
    try:
        connection = get_db_connection()
        result = connection.execute(
            "UPDATE tasks SET done = CASE done WHEN 1 THEN 0 ELSE 1 END WHERE id = ?",
            (task_id,),
        )

        if result.rowcount == 0:
            connection.close()
            return jsonify({"error": "Task not found"}), 404

        connection.commit()
        row = connection.execute(
            "SELECT id, title, done, created_at FROM tasks WHERE id = ?",
            (task_id,),
        ).fetchone()
        connection.close()

        task = {
            "id": row["id"],
            "title": row["title"],
            "done": bool(row["done"]),
            "created_at": row["created_at"],
        }
        return jsonify(task), 200
    except Exception as e:
        print("FULL ERROR TRACEBACK in PUT /tasks/<id>:")
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500


@app.route("/tasks/<int:task_id>", methods=["DELETE"])
def delete_task(task_id):
    # Delete a task by ID.
    try:
        connection = get_db_connection()
        result = connection.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
        connection.commit()
        connection.close()

        if result.rowcount == 0:
            return jsonify({"error": "Task not found"}), 404

        return jsonify({"message": "Task deleted"}), 200
    except Exception as e:
        print("FULL ERROR TRACEBACK in DELETE /tasks/<id>:")
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500


@app.route("/summarize", methods=["POST"])
def summarize_tasks():
    # Summarize current tasks using Claude and return the generated text.
    try:
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            return jsonify({"error": "ANTHROPIC_API_KEY is not set"}), 500

        tasks_list = _fetch_all_tasks()
        task_text = ""
        for t in tasks_list:
            status = "done" if t["done"] else "pending"
            task_text += f"- {t['title']} [{status}]\n"

        prompt = f"Analyze these tasks and give me: 1) A short summary 2) Done vs pending count 3) What to prioritize first and why.\n\nTasks:\n{task_text}"

        client = anthropic.Anthropic(api_key=api_key)
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=1024,
            messages=[{"role": "user", "content": prompt}]
        )

        return jsonify({"summary": response.content[0].text})

    except Exception as e:
        print("FULL ERROR TRACEBACK in POST /summarize:")
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500


if __name__ == '__main__':
    # Ensure database/table exist before accepting requests.
    init_db()
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
