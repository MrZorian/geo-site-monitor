from datetime import datetime
from collections import defaultdict

class MemoryStorage:
    def __init__(self):
        self.logs = []
        self.config = {}
    
    def add_log(self, log_data):
        log_data['id'] = len(self.logs) + 1
        log_data['timestamp'] = datetime.utcnow()
        self.logs.append(log_data)
        if len(self.logs) > 100:
            self.logs = self.logs[-100:]
    
    def get_logs(self, limit=50):
        return sorted(self.logs, key=lambda x: x['timestamp'], reverse=True)[:limit]
    
    def get_stats(self):
        today = datetime.utcnow().date()
        today_logs = [l for l in self.logs if l['timestamp'].date() == today]
        success_count = sum(1 for l in today_logs if l.get('status') == 'success')
        
        return {
            'today_sessions': len(today_logs),
            'total_sessions': len(self.logs),
            'success_rate': round((success_count / len(today_logs) * 100), 2) if today_logs else 0,
            'avg_load_time': 0
        }
    
    def get_stats_by_target(self):
        stats = defaultdict(lambda: {'count': 0, 'success': 0})
        for log in self.logs:
            target = log.get('target_url', 'unknown')
            stats[target]['count'] += 1
            if log.get('status') == 'success':
                stats[target]['success'] += 1
        
        for target in stats:
            stats[target]['success_rate'] = round((stats[target]['success'] / stats[target]['count']) * 100, 1)
        
        return dict(stats)
    
    def set_config(self, key, value):
        self.config[key] = value
    
    def get_config(self, key, default=None):
        return self.config.get(key, default)

storage = MemoryStorage()

class ConfigSetting:
    @staticmethod
    def get(key, default=None):
        return storage.get_config(key, default)
    
    @staticmethod
    def set(key, value):
        storage.set_config(key, value)

# For compatibility
class SessionLog:
    pass

class PageVisit:
    pass

class FakeDB:
    def init_app(self, app):
        pass
    
    def create_all(self):
        pass

db = FakeDB()
