from __future__ import annotations

from flask import Flask, jsonify, redirect, render_template, request, url_for
from flask_login import current_user, login_required, login_user, logout_user

from . import db
from .models import Favorite, User
from .stock_service import StockDataError, StockNotFoundError


def register_routes(app: Flask) -> None:
    @app.get("/")
    def index():
        return render_template("index.html")

    @app.get("/stock/<ticker>")
    def stock_detail(ticker: str):
        return render_template("stock_detail.html", ticker=ticker.upper())

    @app.get("/register")
    def register_page():
        if current_user.is_authenticated:
            return redirect(url_for("index"))
        return render_template("register.html")

    @app.post("/register")
    def register_user():
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        if not username or not password:
            return render_template("register.html", error="Username and password are required")

        existing = User.query.filter_by(username=username).first()
        if existing:
            return render_template("register.html", error="Username already exists")

        user = User(username=username)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()

        login_user(user)
        return redirect(url_for("index"))

    @app.get("/login")
    def login_page():
        if current_user.is_authenticated:
            return redirect(url_for("index"))
        return render_template("login.html")

    @app.post("/login")
    def login_user_route():
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        user = User.query.filter_by(username=username).first()

        if not user or not user.check_password(password):
            return render_template("login.html", error="Invalid credentials")

        login_user(user)
        return redirect(url_for("index"))

    @app.post("/logout")
    @login_required
    def logout_user_route():
        logout_user()
        return redirect(url_for("index"))

    @app.get("/favorites")
    @login_required
    def favorites_page():
        return render_template("favorites.html")

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

    @app.post("/api/favorites")
    @login_required
    def add_favorite():
        payload = request.get_json(silent=True) or {}
        ticker = str(payload.get("ticker", "")).strip().upper()
        if not ticker:
            return jsonify({"error": "Ticker is required"}), 400

        existing = Favorite.query.filter_by(user_id=current_user.id, ticker=ticker).first()
        if existing:
            return jsonify({"error": "Ticker is already in favorites"}), 409

        favorite = Favorite(
            user_id=current_user.id,
            ticker=ticker,
            name=payload.get("name"),
            industry=payload.get("industry"),
            pe_ratio=payload.get("pe_ratio"),
            growth_rate=payload.get("growth_rate"),
            growth_over_pe=payload.get("growth_over_pe"),
            analyst_target_price=payload.get("analyst_target_price"),
        )
        db.session.add(favorite)
        db.session.commit()

        return jsonify({"message": "Favorite saved", "favorite": favorite.to_dict()}), 201

    @app.get("/api/favorites")
    @login_required
    def list_favorites():
        industry_filter = request.args.get("industry", "").strip()
        query = Favorite.query.filter_by(user_id=current_user.id)

        if industry_filter:
            query = query.filter(Favorite.industry.ilike(f"%{industry_filter}%"))

        favorites = query.order_by(Favorite.ticker.asc()).all()
        return jsonify([item.to_dict() for item in favorites])

    @app.delete("/api/favorites/<ticker>")
    @login_required
    def delete_favorite(ticker: str):
        stock = Favorite.query.filter_by(
            user_id=current_user.id, ticker=ticker.upper()
        ).first()
        if not stock:
            return jsonify({"error": "Favorite not found"}), 404

        db.session.delete(stock)
        db.session.commit()
        return jsonify({"message": "Favorite deleted"})
