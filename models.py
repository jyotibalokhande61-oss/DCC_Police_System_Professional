from datetime import datetime
from flask_login import UserMixin
from extensions import db


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False, default="citizen")
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    complaints = db.relationship(
        "Complaint", backref="citizen", lazy=True, foreign_keys="Complaint.created_by"
    )


class Complaint(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    reference = db.Column(db.String(32), unique=True, index=True)
    title = db.Column(db.String(180), nullable=False)
    category = db.Column(db.String(60), nullable=False)
    description = db.Column(db.Text, nullable=False)
    incident_date = db.Column(db.Date, nullable=True)
    location_text = db.Column(db.String(255), nullable=True)
    latitude = db.Column(db.Float, nullable=True)
    longitude = db.Column(db.Float, nullable=True)
    status = db.Column(db.String(40), nullable=False, default="Submitted")
    created_by = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    fir = db.relationship("FIR", backref="complaint", uselist=False, lazy=True)


class FIR(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    complaint_id = db.Column(
        db.Integer, db.ForeignKey("complaint.id"), unique=True, nullable=False
    )
    fir_number = db.Column(db.String(40), unique=True, nullable=False)
    sections = db.Column(db.String(255), nullable=True)
    officer_notes = db.Column(db.Text, nullable=True)
    registered_by = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    registered_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    officer = db.relationship("User", foreign_keys=[registered_by])
