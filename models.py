import datetime
from sqlalchemy.dialects.postgresql import ARRAY
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class User(db.Model):
    """User model for patient records"""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=True)
    email = db.Column(db.String(120), unique=True, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    diagnoses = db.relationship('Diagnosis', backref='patient', lazy=True)

class Diagnosis(db.Model):
    """Diagnosis model to store patient diagnosis history"""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    symptoms = db.Column(ARRAY(db.String(100)), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    results = db.relationship('DiagnosisResult', backref='diagnosis', lazy=True, cascade="all, delete-orphan")

class DiagnosisResult(db.Model):
    """Diagnosis results with probabilities and recommendations"""
    id = db.Column(db.Integer, primary_key=True)
    diagnosis_id = db.Column(db.Integer, db.ForeignKey('diagnosis.id'), nullable=False)
    disease = db.Column(db.String(100), nullable=False)
    probability = db.Column(db.Float, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    
    # Store additional information as JSON
    precautions = db.Column(ARRAY(db.String(200)), nullable=True)
    description = db.Column(db.Text, nullable=True)
    diet = db.Column(db.Text, nullable=True)
    workout = db.Column(db.Text, nullable=True)
    medication = db.Column(db.Text, nullable=True)
