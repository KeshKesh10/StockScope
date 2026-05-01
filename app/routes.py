from __future__ import annotations

import re
import time

from flask import Flask, jsonify, redirect, render_template, request, url_for
from flask_login import current_user, login_required, login_user, logout_user
from werkzeug.security import generate_password_hash

from .auth_user import AuthUser
from .stock_service import StockDataError, StockNotFoundError


def register_routes(app: Flask) -> None:
    def get_store():
        return app.config["STORE"]

    def validate_signup_payload(payload: dict) -> dict[str, str]:
        errors: dict[str, str] = {}
        name = str(payload.get("name", "")).strip()
        email = str(payload.get("email", "")).strip()
        phone = str(payload.get("phone", "")).strip()
        category = str(payload.get("category", "")).strip()

        if not name:
            errors["name"] = "Name Required"

        if not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", email):
            errors["email"] = "Invalid Email"

        phone_digits = re.sub(r"\D", "", phone)
        if len(phone_digits) != 10:
            errors["phone"] = "10-digit Phone Required"

        valid_categories = {"colors", "football", "college"}
        if category.lower() not in valid_categories:
            errors["category"] = "Category must be Colors, Football, or College"

        return errors

    @app.get("/")
    @login_required
    def index():
        return render_template("index.html")

    @app.get("/stock/<ticker>")
    @login_required
    def stock_detail(ticker: str):
        return render_template("stock_detail.html", ticker=ticker.upper())

    @app.get("/register")
    def register_page():
        if current_user.is_authenticated:
            return redirect(url_for("index"))
        return render_template("register.html")

    @app.post("/register")
    def register_user():
        username = request.form.get("username", "").strip().lower()
        password = request.form.get("password", "")
        store = get_store()

        if not username or not password:
            return render_template("register.html", error="Username and password are required")

        existing = store.get_user_by_username(username)
        if existing:
            return render_template("register.html", error="Username already exists")

        item = store.create_user(username=username, password_hash=generate_password_hash(password))
        if not item:
            return render_template("register.html", error="Username already exists")

        login_user(AuthUser.from_item(item))
        return redirect(url_for("index"))

    @app.get("/login")
    def login_page():
        if current_user.is_authenticated:
            return redirect(url_for("index"))
        return render_template("login.html")

    @app.post("/login")
    def login_user_route():
        username = request.form.get("username", "").strip().lower()
        password = request.form.get("password", "")
        store = get_store()
        item = store.get_user_by_username(username)
        user = AuthUser.from_item(item) if item else None

        if not user or not user.check_password(password):
            return render_template("login.html", error="Invalid credentials")

        login_user(user)
        return redirect(url_for("index"))

    @app.post("/logout")
    @login_required
    def logout_user_route():
        logout_user()
        return redirect(url_for("index"))

    @app.get("/industry")
    @login_required
    def industry_page():
        return render_template("industry.html")

    @app.get("/profile")
    @login_required
    def profile_page():
        return render_template("profile.html")

    @app.post("/api/stock")
    def stock_api():
        payload = request.get_json(silent=True) or {}
        symbol = payload.get("ticker", "")
        provider = app.config["STOCK_PROVIDER"]

        try:
            result = provider.get_stock_metrics(symbol)
            return jsonify(result)
        except StockNotFoundError as exc:
            return jsonify({"error": str(exc)}), 404
        except StockDataError as exc:
            return jsonify({"error": str(exc)}), 400
        except Exception:
            return jsonify({"error": "Unexpected provider error"}), 500

    @app.post("/api/auth/register")
    def register_user_api():
        payload = request.get_json(silent=True) or {}
        username = str(payload.get("username", "")).strip().lower()
        password = str(payload.get("password", ""))

        if not username or not password:
            return jsonify({"error": "Username and password are required"}), 400

        store = get_store()
        item = store.create_user(username=username, password_hash=generate_password_hash(password))
        if not item:
            return jsonify({"error": "Username already exists"}), 409

        user = AuthUser.from_item(item)
        login_user(user)
        return jsonify({"message": "User registered", "username": user.username}), 201

    @app.post("/api/auth/login")
    def login_user_api():
        payload = request.get_json(silent=True) or {}
        username = str(payload.get("username", "")).strip().lower()
        password = str(payload.get("password", ""))

        store = get_store()
        item = store.get_user_by_username(username)
        user = AuthUser.from_item(item) if item else None

        if not user or not user.check_password(password):
            return jsonify({"error": "Invalid credentials"}), 401

        login_user(user)
        return jsonify({"message": "Logged in", "username": user.username})

    @app.get("/api/signups")
    def list_signups():
        category = request.args.get("category", "").strip().lower()
        store = get_store()
        result = store.list_signups(category if category else None)
        return jsonify(result)

    @app.post("/api/signups")
    def create_signup():
        payload = request.get_json(silent=True) or {}
        errors = validate_signup_payload(payload)
        if errors:
            return jsonify({"error": "Validation failed", "fieldErrors": errors}), 400

        delay_seconds = max(0, int(app.config.get("POST_SAVE_DELAY_SECONDS", 5)))
        if delay_seconds:
            time.sleep(delay_seconds)

        store = get_store()
        saved = store.create_signup(
            {
                "name": str(payload["name"]).strip(),
                "email": str(payload["email"]).strip().lower(),
                "phone": re.sub(r"\D", "", str(payload["phone"])),
                "category": str(payload["category"]).strip().lower(),
            }
        )
        return jsonify(saved), 201

    @app.post("/api/favorites")
    @login_required
    def add_favorite():
        payload = request.get_json(silent=True) or {}
        ticker = str(payload.get("ticker", "")).strip().upper()
        if not ticker:
            return jsonify({"error": "Ticker is required"}), 400

        store = get_store()
        try:
            favorite = store.add_favorite(
                user_id=str(current_user.id),
                payload={
                    "ticker": ticker,
                    "name": payload.get("name"),
                    "industry": payload.get("industry"),
                    "pe_ratio": payload.get("pe_ratio"),
                    "growth_rate": payload.get("growth_rate"),
                    "growth_over_pe": payload.get("growth_over_pe"),
                    "analyst_target_price": payload.get("analyst_target_price"),
                },
            )
        except ValueError as exc:
            return jsonify({"error": str(exc)}), 409

        return jsonify({"message": "Favorite saved", "favorite": favorite}), 201

    @app.get("/api/favorites")
    @login_required
    def list_favorites():
        industry_filter = request.args.get("industry", "").strip()
        store = get_store()
        favorites = store.list_favorites(str(current_user.id), industry_filter if industry_filter else None)
        return jsonify(favorites)

    @app.delete("/api/favorites/<ticker>")
    @login_required
    def delete_favorite(ticker: str):
        store = get_store()
        deleted = store.delete_favorite(str(current_user.id), ticker.upper())
        if not deleted:
            return jsonify({"error": "Favorite not found"}), 404
        return jsonify({"message": "Favorite deleted"})
