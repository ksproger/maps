from flask import Flask, render_template, request, redirect, url_for, session
from flask_socketio import SocketIO, emit
import secrets
import time

app = Flask(__name__)
app.secret_key = secrets.token_hex(16)
socketio = SocketIO(app)

ADMIN_PASSWORD = "3302"  # поменяй на свой пароль

# Хранилище пользователей: id -> {"lat": , "lon": , "last_update": }
user_locations = {}

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        password = request.form.get("password")
        if password == ADMIN_PASSWORD:
            session["admin"] = True
            return redirect(url_for("admin"))
        return "Неверный пароль"
    return render_template("login.html")

@app.route("/admin")
def admin():
    if not session.get("admin"):
        return redirect(url_for("login"))
    return render_template("admin.html")

@socketio.on("update_location")
def handle_update(data):
    user_id = data.get("id")
    lat = data.get("lat")
    lon = data.get("lon")
    now = time.time()
    if user_id and lat and lon:
        user_locations[user_id] = {
            "lat": lat,
            "lon": lon,
            "last_update": now
        }
        emit("locations", user_locations, broadcast=True)

if __name__ == "__main__":
    socketio.run(app, debug=True, allow_unsafe_werkzeug=True)
