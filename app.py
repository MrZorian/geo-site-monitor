from flask import Flask, render_template, jsonify, request
from flask_socketio import SocketIO, emit
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime
import random
import os
import threading
import time
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

from database import storage, ConfigSetting
from bot import WebsiteMonitor

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-key-123')
socketio = SocketIO(app, cors_allowed_origins="*")

monitor = WebsiteMonitor(app)
current_status = {'is_running': False, 'start_time': None}

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
    stats['target_stats'] = storage.get_stats_by_target()
    stats['proxy_count'] = len([p for p in ConfigSetting.get('PROXY_LIST', '').split(',') if p.strip()]) if ConfigSetting.get('PROXY_LIST') else 0
    return jsonify(stats)

@app.route('/api/logs')
def get_logs():
    logs = storage.get_logs(100)
    result = []
    for log in logs:
        proxy = log.get('proxy_used') or 'direct'
        result.append({
            'id': log.get('id', 0),
            'timestamp': log['timestamp'].strftime('%Y-%m-%d %H:%M:%S'),
            'target_url': log.get('target_url', '-'),
            'proxy_used': proxy[:25] + '...' if len(proxy) > 25 else proxy,
            'pages_visited': log.get('pages_visited', 0),
            'session_duration': round(log.get('session_duration', 0), 0),
            'status': log.get('status', 'unknown'),
            'status_color': 'success' if log.get('status') == 'success' else 'error' if log.get('status') == 'failed' else 'warning'
        })
    return jsonify({'logs': result})

@app.route('/api/settings', methods=['GET', 'POST'])
def api_settings():
    if request.method == 'POST':
        data = request.json
        for key, value in data.items():
            ConfigSetting.set(key, value)
            os.environ[key] = value
        return jsonify({'success': True})
    
    return jsonify({
        'TARGET_URLS': ConfigSetting.get('TARGET_URLS', ''),
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
    
    def run():
        current_status['is_running'] = True
        current_status['start_time'] = datetime.utcnow()
        socketio.emit('session_started', {'time': datetime.utcnow().isoformat()})
        
        try:
            monitor.run_session()
            socketio.emit('session_completed', {'time': datetime.utcnow().isoformat()})
        except Exception as e:
            socketio.emit('session_error', {'error': str(e)})
        finally:
            current_status['is_running'] = False
            current_status['start_time'] = None
    
    threading.Thread(target=run, daemon=True).start()
    return jsonify({'success': True})

@app.route('/api/status')
def get_status():
    return jsonify({
        'is_running': current_status['is_running'],
        'start_time': current_status['start_time'].isoformat() if current_status['start_time'] else None
    })

# Scheduler
scheduler = BackgroundScheduler()

def scheduled_session():
    if current_status['is_running']:
        logger.info("Session already running, skipping")
        return
    
    time.sleep(2)
    
    if current_status['is_running']:
        return
    
    def run():
        current_status['is_running'] = True
        current_status['start_time'] = datetime.utcnow()
        
        try:
            monitor.run_session()
            socketio.emit('session_completed', {'type': 'scheduled'})
        except Exception as e:
            logger.error(f"Session error: {e}")
            socketio.emit('session_error', {'error': str(e)})
        finally:
            current_status['is_running'] = False
            current_status['start_time'] = None
    
    threading.Thread(target=run, daemon=True).start()

def init_scheduler():
    scheduler.remove_all_jobs()
    sessions = int(ConfigSetting.get('SESSIONS_PER_DAY', 35))
    
    for i in range(sessions):
        hour = random.randint(0, 23)
        minute = random.randint(0, 59)
        scheduler.add_job(scheduled_session, 'cron', hour=hour, minute=minute, id=f'session_{i}')
    
    if not scheduler.running:
        scheduler.start()
    logger.info(f"Scheduler started with {sessions} sessions")

init_scheduler()

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=int(os.getenv('PORT', 5000)))
