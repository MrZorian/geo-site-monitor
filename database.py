from datetime import datetime
import json

# Simple in-memory storage - clears when app restarts
class MemoryStorage:
    def __init__(self):
        self.logs = []
        self.config = {}
    
    def add_log(self, log_data):
        """Add a log entry, keep only last 100"""
        log_data['id'] = len(self.logs) + 1
        log_data['timestamp'] = datetime.utcnow()
        self.logs.append(log_data)
        # Keep only last 100 logs
        if len(self.logs) > 100:
            self.logs = self.logs[-100:]
    
    def get_logs(self, limit=50):
        """Get recent logs"""
        return sorted(self.logs, key=lambda x: x['timestamp'], reverse=True)[:limit]
    
    def get_stats(self):
        """Get basic stats"""
        today = datetime.utcnow().date()
        today_logs = [l for l in self.logs if l['timestamp'].date() == today]
        
        success_count = sum(1 for l in today_logs if l.get('status') == 'success')
        
        return {
            'today_sessions': len(today_logs),
            'total_sessions': len(self.logs),
            'success_rate': round((success_count / len(today_logs) * 100), 2) if today_logs else 0,
            'avg_load_time': 0  # Simplified
        }
    
    def set_config(self, key, value):
        self.config[key] = value
    
    def get_config(self, key, default=None):
        return self.config.get(key, default)

# Global instance
storage = MemoryStorage()

# Fake classes for compatibility
class SessionLog:
    @staticmethod
    def query():
        class FakeQuery:
            def filter(self, *args):
                return self
            def order_by(self, *args):
                return self
            def paginate(self, page=1, per_page=20, error_out=False):
                logs = storage.get_logs(per_page)
                class Result:
                    items = logs
                    total = len(storage.logs)
                    pages = 1
                return Result
            def count(self):
                return len(storage.logs)
            def all(self):
                return storage.get_logs(100)
        return FakeQuery()

class ConfigSetting:
    @staticmethod
    def get(key, default=None):
        return storage.get_config(key, default)
    
    @staticmethod
    def set(key, value):
        storage.set_config(key, value)

class PageVisit:
    pass

# Fake db object
class FakeDB:
    def init_app(self, app):
        pass
    
    def create_all(self):
        pass

db = FakeDB()
