from flask import Flask, render_template, jsonify, request
from flask_socketio import SocketIO, emit
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime
import random
import os
import threading
import time

from config import Config
from database import storage, ConfigSetting
from bot import WebsiteMonitor, logger

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-key-123')
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

# Global state
monitor = WebsiteMonitor(app)
current_status = {
    'is_running': False,
    'current_session': None,
    'last_session': None,
    'start_time': None
}

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
    stats['is_running'] = current_status['is_running']
    stats['sessions_per_day'] = ConfigSetting.get('SESSIONS_PER_DAY', '35')
    stats['proxy_count'] = len(ConfigSetting.get('PROXY_LIST', '').split(',')) if ConfigSetting.get('PROXY_LIST') else 0
    return jsonify(stats)

@app.route('/api/logs')
def get_logs():
    logs = storage.get_logs(100)
    result = []
    for log in logs:
        result.append({
            'id': log.get('id', 0),
            'timestamp': log['timestamp'].strftime('%Y-%m-%d %H:%M:%S'),
            'proxy_used': log.get('proxy_used', 'direct')[:30] + '...' if len(log.get('proxy_used', '')) > 30 else log.get('proxy_used', 'direct'),
            'pages_visited': log.get('pages_visited', 0),
            'session_duration': round(log.get('session_duration', 0), 1),
            'avg_load_time': round(log.get('avg_load_time', 0), 2) if log.get('avg_load_time') else None,
            'errors_count': len(log.get('errors', [])),
            'status': log.get('status', 'unknown'),
            'status_color': 'success' if log.get('status') == 'success' else 'error' if log.get('status') == 'failed' else 'warning'
        })
    return jsonify({'logs': result, 'total': len(storage.logs)})

@app.route('/api/settings', methods=['GET', 'POST'])
def api_settings():
    if request.method == 'POST':
        data = request.json
        for key, value in data.items():
            ConfigSetting.set(key, value)
        socketio.emit('settings_updated', {'message': 'Settings saved'})
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
    if current_status['is_running']:
        return jsonify({'success': False, 'error': 'Session already running'}), 429
    
    def run_with_updates():
        current_status['is_running'] = True
        current_status['start_time'] = datetime.utcnow()
        socketio.emit('session_started', {
            'timestamp': datetime.utcnow().isoformat(),
            'message': 'Session started'
        })
        
        try:
            monitor.run_session()
            current_status['last_session'] = {
                'timestamp': datetime.utcnow().isoformat(),
                'status': 'completed'
            }
            socketio.emit('session_completed', {
                'timestamp': datetime.utcnow().isoformat(),
                'message': 'Session completed successfully'
            })
        except Exception as e:
            socketio.emit('session_error', {
                'timestamp': datetime.utcnow().isoformat(),
                'error': str(e)
            })
        finally:
            current_status['is_running'] = False
            current_status['start_time'] = None
            # Refresh stats for all clients
            socketio.emit('stats_update', storage.get_stats())
    
    thread = threading.Thread(target=run_with_updates)
    thread.daemon = True
    thread.start()
    
    return jsonify({'success': True, 'message': 'Session started'})

@app.route('/api/status')
def get_status():
    return jsonify({
        'is_running': current_status['is_running'],
        'start_time': current_status['start_time'].isoformat() if current_status['start_time'] else None,
        'last_session': current_status['last_session'],
        'uptime': 'Running' if current_status['is_running'] else 'Idle'
    })

@app.route('/api/test-proxy', methods=['POST'])
def test_proxy():
    data = request.json
    proxy = data.get('proxy')
    
    def test_async():
        try:
            import requests
            proxies = {'http': proxy, 'https': proxy}
            response = requests.get('https://httpbin.org/ip', proxies=proxies, timeout=10)
            socketio.emit('proxy_test_result', {
                'proxy': proxy[:20] + '...',
                'success': True,
                'ip': response.json().get('origin', 'unknown')
            })
        except Exception as e:
            socketio.emit('proxy_test_result', {
                'proxy': proxy[:20] + '...',
                'success': False,
                'error': str(e)[:50]
            })
    
    thread = threading.Thread(target=test_async)
    thread.daemon = True
    thread.start()
    
    return jsonify({'success': True, 'message': 'Testing proxy...'})

# Background scheduler
scheduler = BackgroundScheduler()

def scheduled_session():
    if current_status['is_running']:
        logger.info("Skipping scheduled session - already running")
        return
    
    def run_scheduled():
        current_status['is_running'] = True
        current_status['start_time'] = datetime.utcnow()
        socketio.emit('session_started', {
            'timestamp': datetime.utcnow().isoformat(),
            'message': 'Scheduled session started',
            'type': 'scheduled'
        })
        
        try:
            monitor.run_session()
            socketio.emit('session_completed', {
                'timestamp': datetime.utcnow().isoformat(),
                'message': 'Scheduled session completed',
                'type': 'scheduled'
            })
        except Exception as e:
            logger.error(f"Scheduled session failed: {e}")
            socketio.emit('session_error', {
                'timestamp': datetime.utcnow().isoformat(),
                'error': str(e),
                'type': 'scheduled'
            })
        finally:
            current_status['is_running'] = False
            current_status['start_time'] = None
            socketio.emit('stats_update', storage.get_stats())
    
    thread = threading.Thread(target=run_scheduled)
    thread.daemon = True
    thread.start()

def init_scheduler():
    scheduler.remove_all_jobs()
    sessions_per_day = int(ConfigSetting.get('SESSIONS_PER_DAY', 35))
    
    for i in range(sessions_per_day):
        hour = random.randint(0, 23)
        minute = random.randint(0, 59)
        scheduler.add_job(
            scheduled_session,
            'cron',
            hour=hour,
            minute=minute,
            id=f'session_{i}',
            replace_existing=True
        )
    
    if not scheduler.running:
        scheduler.start()
    logger.info(f"Scheduler initialized with {sessions_per_day} daily sessions")

if __name__ == '__main__':
    init_scheduler()
    socketio.run(app, host='0.0.0.0', port=int(os.getenv('PORT', 5000)), debug=False)
else:
    init_scheduler()
