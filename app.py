import os
from datetime import datetime
from functools import wraps

import click
from dotenv import load_dotenv
from flask import Flask, abort, flash, redirect, render_template, request, url_for
from flask_login import (
    LoginManager, current_user, login_required, login_user, logout_user
)
from flask_wtf.csrf import CSRFProtect
from werkzeug.security import check_password_hash, generate_password_hash

from extensions import db
from models import Complaint, FIR, User

load_dotenv()


def create_app():
    app = Flask(__name__)
    app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "dev-only-change-me")
    app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv(
        "DATABASE_URL", "sqlite:///dcc_police.db"
    )
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["MAX_CONTENT_LENGTH"] = 5 * 1024 * 1024

    db.init_app(app)
    CSRFProtect(app)

    login_manager = LoginManager()
    login_manager.login_view = "login"
    login_manager.login_message_category = "info"
    login_manager.init_app(app)

    @login_manager.user_loader
    def load_user(user_id):
        return db.session.get(User, int(user_id))

    def role_required(*roles):
        def decorator(view):
            @wraps(view)
            @login_required
            def wrapped(*args, **kwargs):
                if current_user.role not in roles:
                    abort(403)
                return view(*args, **kwargs)
            return wrapped
        return decorator

    @app.context_processor
    def inject_globals():
        return {"now_year": datetime.now().year}

    @app.route("/")
    def home():
        return render_template("index.html")

    @app.route("/register", methods=["GET", "POST"])
    def register():
        if current_user.is_authenticated:
            return redirect(url_for("dashboard"))
        if request.method == "POST":
            name = request.form.get("name", "").strip()
            email = request.form.get("email", "").strip().lower()
            password = request.form.get("password", "")
            if not name or not email or len(password) < 8:
                flash("Enter your name, a valid email, and a password of at least 8 characters.", "error")
                return render_template("auth/register.html")
            if User.query.filter_by(email=email).first():
                flash("An account with that email already exists.", "error")
                return render_template("auth/register.html")
            user = User(
                name=name,
                email=email,
                password_hash=generate_password_hash(password),
                role="citizen",
            )
            db.session.add(user)
            db.session.commit()
            flash("Account created. You can now sign in.", "success")
            return redirect(url_for("login"))
        return render_template("auth/register.html")

    @app.route("/login", methods=["GET", "POST"])
    def login():
        if current_user.is_authenticated:
            return redirect(url_for("dashboard"))
        if request.method == "POST":
            email = request.form.get("email", "").strip().lower()
            password = request.form.get("password", "")
            user = User.query.filter_by(email=email).first()
            if user and check_password_hash(user.password_hash, password):
                login_user(user)
                flash("Welcome back.", "success")
                return redirect(url_for("dashboard"))
            flash("Email or password was not recognized.", "error")
        return render_template("auth/login.html")

    @app.route("/logout", methods=["POST"])
    @login_required
    def logout():
        logout_user()
        flash("You have been signed out.", "success")
        return redirect(url_for("home"))

    @app.route("/dashboard")
    @login_required
    def dashboard():
        if current_user.role in ("officer", "admin"):
            complaints = Complaint.query.order_by(Complaint.created_at.desc()).all()
            counts = {
                "total": Complaint.query.count(),
                "pending": Complaint.query.filter_by(status="Submitted").count(),
                "in_progress": Complaint.query.filter_by(status="Under Review").count(),
                "resolved": Complaint.query.filter_by(status="Resolved").count(),
            }
        else:
            complaints = Complaint.query.filter_by(
                created_by=current_user.id
            ).order_by(Complaint.created_at.desc()).all()
            counts = {
                "total": len(complaints),
                "pending": sum(c.status == "Submitted" for c in complaints),
                "in_progress": sum(c.status == "Under Review" for c in complaints),
                "resolved": sum(c.status == "Resolved" for c in complaints),
            }
        if current_user.role in ("officer", "admin"):
            return render_template("police/dashboard.html", complaints=complaints, counts=counts)
        return render_template("citizen/dashboard.html", complaints=complaints, counts=counts)

    @app.route("/complaints/new", methods=["GET", "POST"])
    @role_required("citizen")
    def new_complaint():
        categories = ["Missing Person", "Theft", "Harassment", "Lost Property", "Cybercrime", "Other"]
        if request.method == "POST":
            title = request.form.get("title", "").strip()
            category = request.form.get("category", "")
            description = request.form.get("description", "").strip()
            incident_date = request.form.get("incident_date") or None
            location_text = request.form.get("location_text", "").strip()
            lat_raw = request.form.get("latitude", "").strip()
            lon_raw = request.form.get("longitude", "").strip()

            if not title or category not in categories or len(description) < 20:
                flash("Complete all required fields. Description must contain at least 20 characters.", "error")
                return render_template("complaints/new.html", categories=categories)

            latitude = longitude = None
            try:
                if lat_raw and lon_raw:
                    latitude, longitude = float(lat_raw), float(lon_raw)
                    if not (-90 <= latitude <= 90 and -180 <= longitude <= 180):
                        raise ValueError
            except ValueError:
                flash("The supplied map coordinates are invalid. You can leave them blank.", "error")
                return render_template("complaints/new.html", categories=categories)

            parsed_date = None
            if incident_date:
                try:
                    parsed_date = datetime.strptime(incident_date, "%Y-%m-%d").date()
                except ValueError:
                    flash("Please enter a valid incident date.", "error")
                    return render_template("complaints/new.html", categories=categories)

            complaint = Complaint(
                title=title,
                category=category,
                description=description,
                incident_date=parsed_date,
                location_text=location_text or None,
                latitude=latitude,
                longitude=longitude,
                created_by=current_user.id,
                status="Submitted",
            )
            db.session.add(complaint)
            db.session.commit()
            complaint.reference = f"DCC-{datetime.now().year}-{complaint.id:05d}"
            db.session.commit()
            flash(f"Complaint submitted. Your reference is {complaint.reference}.", "success")
            return redirect(url_for("complaint_detail", complaint_id=complaint.id))
        return render_template("complaints/new.html", categories=categories)

    @app.route("/complaints/<int:complaint_id>")
    @login_required
    def complaint_detail(complaint_id):
        complaint = db.get_or_404(Complaint, complaint_id)
        if current_user.role == "citizen" and complaint.created_by != current_user.id:
            abort(403)
        return render_template("complaints/detail.html", complaint=complaint)

    @app.route("/complaints/<int:complaint_id>/status", methods=["POST"])
    @role_required("officer", "admin")
    def update_status(complaint_id):
        complaint = db.get_or_404(Complaint, complaint_id)
        allowed = {"Submitted", "Under Review", "Investigation", "Resolved", "Closed"}
        status = request.form.get("status")
        if status not in allowed:
            abort(400)
        complaint.status = status
        complaint.updated_at = datetime.utcnow()
        db.session.commit()
        flash("Complaint status updated.", "success")
        return redirect(url_for("complaint_detail", complaint_id=complaint.id))

    @app.route("/complaints/<int:complaint_id>/fir", methods=["POST"])
    @role_required("officer", "admin")
    def create_fir(complaint_id):
        complaint = db.get_or_404(Complaint, complaint_id)
        if complaint.fir:
            flash("An FIR record already exists for this complaint.", "info")
            return redirect(url_for("complaint_detail", complaint_id=complaint.id))
        sections = request.form.get("sections", "").strip()
        notes = request.form.get("officer_notes", "").strip()
        fir = FIR(
            complaint_id=complaint.id,
            fir_number=f"DEMO-FIR-{datetime.now().year}-{complaint.id:05d}",
            sections=sections or None,
            officer_notes=notes or None,
            registered_by=current_user.id,
        )
        db.session.add(fir)
        complaint.status = "Investigation"
        complaint.updated_at = datetime.utcnow()
        db.session.commit()
        flash("Demonstration FIR record created. This is not an official police FIR number.", "success")
        return redirect(url_for("complaint_detail", complaint_id=complaint.id))

    @app.errorhandler(403)
    def forbidden(_error):
        return render_template("errors/403.html"), 403

    @app.errorhandler(404)
    def not_found(_error):
        return render_template("errors/404.html"), 404

    @app.cli.command("init-db")
    def init_db():
        """Create database tables."""
        db.create_all()
        click.echo("Database tables created.")

    @app.cli.command("create-officer")
    @click.option("--name", prompt=True, help="Officer display name")
    @click.option("--email", prompt=True, help="Officer email address")
    @click.password_option(confirmation_prompt=True)
    def create_officer(name, email, password):
        """Create an officer account for local demonstration."""
        email = email.strip().lower()
        if User.query.filter_by(email=email).first():
            click.echo("A user with that email already exists.")
            return
        user = User(
            name=name.strip(),
            email=email,
            password_hash=generate_password_hash(password),
            role="officer",
        )
        db.session.add(user)
        db.session.commit()
        click.echo(f"Officer account created for {email}.")

    return app


app = create_app()

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=os.getenv("FLASK_DEBUG", "true").lower() == "true")
