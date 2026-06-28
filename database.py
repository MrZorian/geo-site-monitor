def add_log(self, log_data):
    """Add a log entry, keep only last 100"""
    log_data['id'] = len(self.logs) + 1
    log_data['timestamp'] = datetime.utcnow()
    self.logs.append(log_data)
    if len(self.logs) > 100:
        self.logs = self.logs[-100:]

def get_stats_by_target(self):
    """Get stats grouped by target URL"""
    from collections import defaultdict
    stats = defaultdict(lambda: {'count': 0, 'success': 0, 'avg_load': 0})
    
    for log in self.logs:
        target = log.get('target_url', 'unknown')
        stats[target]['count'] += 1
        if log.get('status') == 'success':
            stats[target]['success'] += 1
        if log.get('avg_load_time'):
            stats[target]['avg_load'] += log['avg_load_time']
    
    # Calculate averages
    for target in stats:
        if stats[target]['count'] > 0:
            stats[target]['avg_load'] = stats[target]['avg_load'] / stats[target]['count']
            stats[target]['success_rate'] = (stats[target]['success'] / stats[target]['count']) * 100
    
    return dict(stats)
