from flask import Flask, render_template, jsonify, request
from flask_socketio import SocketIO
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime
import random
import os

from config import Config
from database import storage, SessionLog, ConfigSetting
from bot import WebsiteMonitor

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-key-123')

# No database needed
socketio = SocketIO(app, cors_allowed_origins="*")

# Initialize bot
monitor = WebsiteMonitor(app)

@app.route('/')
def dashboard():
    return render_template('dashboard.html')

@app.route('/logs')
def logs():
    return render_template('logs.html')

@app.route('/settings')
def settings():
    return render_template('settings.html')

@app.route('/api/stats')
def get_stats():
    stats = storage.get_stats()
    stats['target_url'] = ConfigSetting.get('TARGET_URL', 'Not set')
    return jsonify(stats)

@app.route('/api/logs')
def get_logs():
    logs = storage.get_logs(50)
    result = []
    for log in logs:
        result.append({
            'id': log.get('id', 0),
            'timestamp': log['timestamp'].strftime('%Y-%m-%d %H:%M:%S'),
            'proxy_used': log.get('proxy_used', 'direct'),
            'pages_visited': log.get('pages_visited', 0),
            'session_duration': round(log.get('session_duration', 0), 2),
            'avg_load_time': round(log.get('avg_load_time', 0), 2) if log.get('avg_load_time') else None,
            'errors_found': log.get('errors', []),
            'status': log.get('status', 'unknown')
        })
    
    return jsonify({
        'logs': result,
        'total': len(storage.logs),
        'pages': 1,
        'current_page': 1
    })

@app.route('/api/settings', methods=['GET', 'POST'])
def api_settings():
    if request.method == 'POST':
        data = request.json
        for key, value in data.items():
            ConfigSetting.set(key, value)
        return jsonify({'success': True, 'message': 'Settings updated'})
    
    return jsonify({
        'TARGET_URL': ConfigSetting.get('TARGET_URL', ''),
        'PROXY_LIST': ConfigSetting.get('PROXY_LIST', ''),
        'SESSIONS_PER_DAY': ConfigSetting.get('SESSIONS_PER_DAY', '35'),
        'MIN_SESSION_DURATION': ConfigSetting.get('MIN_SESSION_DURATION', '240'),
        'MAX_SESSION_DURATION': ConfigSetting.get('MAX_SESSION_DURATION', '300'),
        'PAGES_PER_SESSION': ConfigSetting.get('PAGES_PER_SESSION', '4'),
        'HEADLESS': ConfigSetting.get('HEADLESS', 'true'),
        'USER_AGENT_ROTATION': ConfigSetting.get('USER_AGENT_ROTATION', 'true')
    })

@app.route('/api/run-now', methods=['POST'])
def run_now():
    try:
        import threading
        thread = threading.Thread(target=monitor.run_session)
        thread.daemon = True
        thread.start()
        return jsonify({'success': True, 'message': 'Session started'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/test-proxy', methods=['POST'])
def test_proxy():
    data = request.json
    proxy = data.get('proxy')
    
    try:
        import requests
        proxies = {'http': proxy, 'https': proxy}
        response = requests.get('https://httpbin.org/ip', proxies=proxies, timeout=10)
        return jsonify({'success': True, 'message': 'Proxy working', 'response': response.json()})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

# Background scheduler
scheduler = BackgroundScheduler()

def scheduled_session():
    monitor.run_session()
    socketio.emit('session_complete', {'timestamp': datetime.utcnow().isoformat()})

def init_scheduler():
    scheduler.remove_all_jobs()
    sessions_per_day = int(ConfigSetting.get('SESSIONS_PER_DAY', 35))
    
    for i in range(sessions_per_day):
        hour = random.randint(0, 23)
        minute = random.randint(0, 59)
        scheduler.add_job(scheduled_session, 'cron', hour=hour, minute=minute, id=f'session_{i}', replace_existing=True)
    
    if not scheduler.running:
        scheduler.start()

@app.before_request
def check_scheduler():
    if not scheduler.running:
        init_scheduler()

if __name__ == '__main__':
    init_scheduler()
    socketio.run(app, host='0.0.0.0', port=int(os.getenv('PORT', 5000)))
else:
    init_scheduler()
