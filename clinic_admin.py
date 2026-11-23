"""Secure, clinic-scoped admin blueprint for the dental chatbot.

Integrates with the existing clinics.py get_clinic/save_clinic/DB_PATH API.
Requires Flask. Uses Flask's signed session and Werkzeug password hashing.
"""
from __future__ import annotations

import hmac
import secrets
import sqlite3
from functools import wraps
from pathlib import Path
from typing import Callable

from flask import (Blueprint, abort, current_app, flash, redirect, render_template,
                   request, session, url_for)
from werkzeug.security import check_password_hash, generate_password_hash


def create_admin_blueprint(get_clinic: Callable, save_clinic: Callable,
                           db_path: str | Path, url_prefix: str = "/admin") -> Blueprint:
    bp = Blueprint("clinic_admin", __name__, template_folder="templates",
                   static_folder="static", url_prefix=url_prefix)
    db_path = Path(db_path)

    def connect():
        db_path.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("""CREATE TABLE IF NOT EXISTS clinic_admin_users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            password_hash TEXT NOT NULL,
            clinic_id TEXT NOT NULL,
            active INTEGER NOT NULL DEFAULT 1,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        )""")
        conn.commit()
        return conn

    def current_user():
        uid = session.get("clinic_admin_uid")
        if not uid:
            return None
        with connect() as db:
            return db.execute("SELECT * FROM clinic_admin_users WHERE id=? AND active=1", (uid,)).fetchone()

    def login_required(fn):
        @wraps(fn)
        def wrapped(*args, **kwargs):
            if current_user() is None:
                return redirect(url_for("clinic_admin.login", next=request.path))
            return fn(*args, **kwargs)
        return wrapped

    def csrf_token():
        if "clinic_admin_csrf" not in session:
            session["clinic_admin_csrf"] = secrets.token_urlsafe(32)
        return session["clinic_admin_csrf"]

    @bp.before_request
    def protect_posts():
        if request.method == "POST":
            sent = request.form.get("csrf_token", "")
            expected = session.get("clinic_admin_csrf", "")
            if not expected or not hmac.compare_digest(sent, expected):
                abort(400, "Érvénytelen vagy lejárt űrlap-token. Frissítsd az oldalt.")

    @bp.context_processor
    def inject_globals():
        return {"csrf_token": csrf_token, "admin_user": current_user()}

    @bp.get("/login")
    def login():
        if current_user():
            return redirect(url_for("clinic_admin.dashboard"))
        return render_template("clinic_admin/login.html")

    @bp.post("/login")
    def login_post():
        username = request.form.get("username", "").strip().lower()
        password = request.form.get("password", "")
        with connect() as db:
            user = db.execute("SELECT * FROM clinic_admin_users WHERE username=? AND active=1", (username,)).fetchone()
        if not user or not check_password_hash(user["password_hash"], password):
            flash("Hibás felhasználónév vagy jelszó.", "error")
            return redirect(url_for("clinic_admin.login"))
        session.clear()
        session["clinic_admin_uid"] = user["id"]
        session["clinic_admin_csrf"] = secrets.token_urlsafe(32)
        return redirect(url_for("clinic_admin.dashboard"))

    @bp.post("/logout")
    @login_required
    def logout():
        session.clear()
        return redirect(url_for("clinic_admin.login"))

    @bp.get("/")
    @bp.get("/clinic")
    @login_required
    def dashboard():
        user = current_user()
        try:
            clinic = get_clinic(user["clinic_id"])
        except ValueError:
            abort(404, "A rendelő konfigurációja nem található.")
        treatments = clinic.get("treatments", {})
        return render_template("clinic_admin/dashboard.html", clinic=clinic,
                               clinic_id=user["clinic_id"], treatments=treatments)

    @bp.post("/clinic/save")
    @login_required
    def save_settings():
        user = current_user()
        clinic_id = user["clinic_id"]  # Never accept clinic_id from the browser.
        clinic = dict(get_clinic(clinic_id))
        clinic.update({
            "name": request.form.get("name", "").strip(),
            "address": request.form.get("address", "").strip(),
            "phone": request.form.get("phone", "").strip(),
            "timezone": request.form.get("timezone", "Europe/Budapest").strip(),
            "calendar_id": request.form.get("calendar_id", "primary").strip(),
            "slot_interval_minutes": _int_range(request.form.get("slot_interval_minutes"), 30, 5, 240),
        })
        start = request.form.get("opening_start", "09:00")
        end = request.form.get("opening_end", "17:00")
        weekdays = [int(x) for x in request.form.getlist("weekdays") if x in {str(i) for i in range(7)}]
        if not _valid_time(start) or not _valid_time(end) or start >= end:
            flash("Ellenőrizd a nyitvatartási időket.", "error")
            return redirect(url_for("clinic_admin.dashboard") + "#clinic")
        clinic["opening_hours"] = {"start": start, "end": end, "weekdays": weekdays}
        try:
            save_clinic(clinic_id, clinic)
        except Exception as exc:
            current_app.logger.exception("Clinic settings save failed")
            flash(f"Nem sikerült menteni: {exc}", "error")
        else:
            flash("A rendelő adatai elmentve.", "success")
        return redirect(url_for("clinic_admin.dashboard") + "#clinic")

    @bp.post("/treatments/save")
    @login_required
    def save_treatment():
        user = current_user()
        clinic_id = user["clinic_id"]
        clinic = dict(get_clinic(clinic_id))
        treatments = dict(clinic.get("treatments", {}))
        key = request.form.get("key", "").strip().lower().replace(" ", "_")
        if not key or not key.replace("_", "").replace("-", "").isalnum():
            flash("A kezelés azonosítója csak betűt, számot, kötőjelet és aláhúzást tartalmazhat.", "error")
            return redirect(url_for("clinic_admin.dashboard") + "#treatments")
        duration = _int_range(request.form.get("duration"), 30, 5, 480)
        treatments[key] = {
            "names": {"hun": request.form.get("name_hu", "").strip(),
                      "de": request.form.get("name_de", "").strip(),
                      "en": request.form.get("name_en", "").strip()},
            "price": request.form.get("price", "").strip(),
            "duration": duration,
        }
        clinic["treatments"] = treatments
        save_clinic(clinic_id, clinic)
        flash("A kezelés elmentve.", "success")
        return redirect(url_for("clinic_admin.dashboard") + "#treatments")

    @bp.post("/treatments/delete/<key>")
    @login_required
    def delete_treatment(key):
        user = current_user()
        clinic = dict(get_clinic(user["clinic_id"]))
        treatments = dict(clinic.get("treatments", {}))
        if key not in treatments:
            abort(404)
        treatments.pop(key)
        clinic["treatments"] = treatments
        save_clinic(user["clinic_id"], clinic)
        flash("A kezelés törölve.", "success")
        return redirect(url_for("clinic_admin.dashboard") + "#treatments")

    return bp


def _int_range(value, default, minimum, maximum):
    try:
        return max(minimum, min(maximum, int(value)))
    except (TypeError, ValueError):
        return default


def _valid_time(value):
    if not isinstance(value, str) or len(value) != 5 or value[2] != ":":
        return False
    try:
        hour, minute = map(int, value.split(":"))
        return 0 <= hour <= 23 and 0 <= minute <= 59
    except ValueError:
        return False


def create_clinic_admin(db_path: str | Path, clinic_id: str, username: str,
                        password: str) -> None:
    """Provision an admin login for an existing clinic. Run from trusted CLI only."""
    if len(password) < 12:
        raise ValueError("A jelszónak legalább 12 karakteresnek kell lennie.")
    username = username.strip().lower()
    if not username or "@" not in username:
        raise ValueError("Érvényes e-mail-címet adj meg felhasználónévként.")
    path = Path(db_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(path) as db:
        db.execute("""CREATE TABLE IF NOT EXISTS clinic_admin_users (
            id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT NOT NULL UNIQUE,
            password_hash TEXT NOT NULL, clinic_id TEXT NOT NULL,
            active INTEGER NOT NULL DEFAULT 1,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP)""")
        db.execute("INSERT INTO clinic_admin_users(username,password_hash,clinic_id) VALUES(?,?,?)",
                   (username, generate_password_hash(password), clinic_id))
