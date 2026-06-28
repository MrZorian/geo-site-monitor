from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import json

db = SQLAlchemy()

class SessionLog(db.Model):
    __tablename__ = 'session_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    proxy_used = db.Column(db.String(500))
    pages_visited = db.Column(db.Integer)
    session_duration = db.Column(db.Float)  # seconds
    avg_load_time = db.Column(db.Float)
    errors_found = db.Column(db.Text)  # JSON string
    status = db.Column(db.String(50))  # success, failed, running
    
    def to_dict(self):
        return {
            'id': self.id,
            'timestamp': self.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
            'proxy_used': self.proxy_used,
            'pages_visited': self.pages_visited,
            'session_duration': round(self.session_duration, 2),
            'avg_load_time': round(self.avg_load_time, 2) if self.avg_load_time else None,
            'errors_found': json.loads(self.errors_found) if self.errors_found else [],
            'status': self.status
        }

class ConfigSetting(db.Model):
    __tablename__ = 'config_settings'
    
    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(100), unique=True)
    value = db.Column(db.Text)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    @staticmethod
    def get(key, default=None):
        setting = ConfigSetting.query.filter_by(key=key).first()
        return setting.value if setting else default
    
    @staticmethod
    def set(key, value):
        setting = ConfigSetting.query.filter_by(key=key).first()
        if setting:
            setting.value = str(value)
        else:
            setting = ConfigSetting(key=key, value=str(value))
            db.session.add(setting)
        db.session.commit()

class PageVisit(db.Model):
    __tablename__ = 'page_visits'
    
    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.Integer, db.ForeignKey('session_logs.id'))
    url = db.Column(db.String(1000))
    load_time = db.Column(db.Float)
    status_code = db.Column(db.Integer)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)