from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from . import db

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(120), nullable=False)
    is_admin = db.Column(db.Boolean, default=False, nullable=False)
    is_approved = db.Column(db.Boolean, default=False, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    environments = db.relationship('Environment', backref='admin', lazy=True)
    wireless_scans = db.relationship('WirelessScan', backref='uploader', lazy=True)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def __repr__(self):
        return f'<User {self.username}>'

class Environment(db.Model):
    __tablename__ = 'environments'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    wireless_scans = db.relationship('WirelessScan', backref='environment', lazy=True, cascade='all, delete-orphan')
    
    # Ensure environment names are unique per admin
    __table_args__ = (db.UniqueConstraint('name', 'created_by', name='_environment_name_admin_uc'),)
    
    def __repr__(self):
        return f'<Environment {self.name}>'

class WirelessScan(db.Model):
    __tablename__ = 'wireless_scans'
    
    id = db.Column(db.Integer, primary_key=True)
    environment_id = db.Column(db.Integer, db.ForeignKey('environments.id'), nullable=False)
    bssid = db.Column(db.String(17), nullable=False)  # MAC address format: AA:BB:CC:DD:EE:FF
    ssid = db.Column(db.String(32), nullable=False)   # SSID max length is 32 bytes
    quality = db.Column(db.Integer)
    signal = db.Column(db.Integer)
    channel = db.Column(db.Integer)
    encryption = db.Column(db.String(50))
    timestamp = db.Column(db.DateTime, nullable=False)
    remarks = db.Column(db.Text)
    rogue_ap_potential = db.Column(db.Boolean, default=False, nullable=False)  # Rogue AP potential flag
    uploaded_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Prevent duplicates: unique constraint on environment_id, bssid, ssid
    __table_args__ = (db.UniqueConstraint('environment_id', 'bssid', 'ssid', name='_scan_dedup_uc'),)
    
    def __repr__(self):
        return f'<WirelessScan {self.bssid} - {self.ssid}>'