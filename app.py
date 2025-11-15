from flask import Flask, render_template, request, make_response, redirect, url_for
from flask_socketio import SocketIO, emit
import uuid
import time

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")

# --- Хранилища ---
users = {}   # {uid: {"lat":..., "lon":..., "last_update": ..., "name": ...}}
names = {}   # {uid: "Имя"}  <-- отдельный словарь для админа
ADMIN_PASSWORD = "admin123"

# --- Страницы ---

@app.route("/")
def index():
    user_id = request.cookies.get("uid")
    if not user_id:
        user_id = str(uuid.uuid4())
    resp = make_response(render_template("index.html"))
    resp.set_cookie("uid", user_id, max_age=60*60*24*365)
    return resp

@app.route("/login", methods=["GET","POST"])
def login():
    if request.method=="POST":
        if request.form.get("password")==ADMIN_PASSWORD:
            resp = make_response(redirect(url_for("admin_page")))
            resp.set_cookie("admin","true",max_age=60*60*4)
            return resp
        return render_template("login.html", error="Неверный пароль")
    return render_template("login.html")

@app.route("/admin")
def admin_page():
    if request.cookies.get("admin")=="true":
        return render_template("admin.html")
    return redirect(url_for("login"))

# --- API админа ---

@app.route("/admin/clear", methods=["POST"])
def clear_users():
    if request.cookies.get("admin") != "true":
        return "Unauthorized", 401
    users.clear()
    socketio.emit("locations", users)
    return "OK", 200

@app.route("/admin/delete/<uid>", methods=["POST"])
def delete_user(uid):
    if request.cookies.get("admin") != "true":
        return "Unauthorized", 401
    if uid in users:
        del users[uid]
        socketio.emit("locations", users)
    return "OK", 200

@app.route("/admin/rename/<uid>", methods=["POST"])
def rename_user(uid):
    if request.cookies.get("admin") != "true":
        return "Unauthorized", 401
    new_name = request.json.get("name")
    if uid in users:
        users[uid]["name"] = new_name
        names[uid] = new_name  # сохраняем и в словарь имен
        socketio.emit("locations", users)
    return "OK", 200

@app.route("/admin/setname/<uid>", methods=["POST"])
def set_name(uid):
    if request.cookies.get("admin") != "true":
        return "Unauthorized", 401
    new_name = request.json.get("name")
    if not new_name:
        return "Bad Request", 400
    names[uid] = new_name
    if uid in users:
        users[uid]["name"] = new_name
        socketio.emit("locations", users)
    return "OK", 200

# --- WebSocket ---

@socketio.on("coords")
def handle_coords(data):
    uid = data["uid"]
    name = users.get(uid, {}).get("name") or names.get(uid)
    users[uid] = {
        "lat": data["lat"],
        "lon": data["lon"],
        "last_update": time.time(),
        "name": name
    }
    emit("locations", users, broadcast=True)

# --- Запуск ---
if __name__ == "__main__":
    socketio.run(app, host="0.0.0.0", port=5000, debug=True, allow_unsafe_werkzeug=True)
