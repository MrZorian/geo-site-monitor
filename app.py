from flask import Flask, render_template, jsonify, request, redirect, url_for
from flask_socketio import SocketIO, emit
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime, timedelta
import json
import os
import random  # BUG FIX #1: Added missing import

from config import Config
from database import db, SessionLog, PageVisit, ConfigSetting
from bot import WebsiteMonitor

app = Flask(__name__)
app.config.from_object(Config)
db.init_app(app)
socketio = SocketIO(app, cors_allowed_origins="*")

# Initialize bot
monitor = WebsiteMonitor(app)

def create_tables():
    with app.app_context():
        db.create_all()

@app.route('/')
def dashboard():
    return render_template('dashboard.html')

@app.route('/logs')
def logs():
    return render_template('logs.html')

@app.route('/settings')
def settings():
    return render_template('settings.html')

# API Endpoints
@app.route('/api/stats')
def get_stats():
    with app.app_context():
        # Today's stats
        today = datetime.utcnow().date()
        today_start = datetime.combine(today, datetime.min.time())
        
        today_sessions = SessionLog.query.filter(SessionLog.timestamp >= today_start).all()
        total_sessions = SessionLog.query.count()
        
        success_count = sum(1 for s in today_sessions if s.status == 'success')
        
        avg_load_time = 0
        if today_sessions:
            load_times = [s.avg_load_time for s in today_sessions if s.avg_load_time]
            avg_load_time = sum(load_times) / len(load_times) if load_times else 0
        
        return jsonify({
            'today_sessions': len(today_sessions),
            'total_sessions': total_sessions,
            'success_rate': round((success_count / len(today_sessions) * 100), 2) if today_sessions else 0,
            'avg_load_time': round(avg_load_time, 2),
            'target_url': ConfigSetting.get('TARGET_URL', 'Not set'),
            'sessions_per_day': ConfigSetting.get('SESSIONS_PER_SESSION', '35')
        })

@app.route('/api/logs')
def get_logs():
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    
    with app.app_context():
        pagination = SessionLog.query.order_by(SessionLog.timestamp.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        return jsonify({
            'logs': [log.to_dict() for log in pagination.items],
            'total': pagination.total,
            'pages': pagination.pages,
            'current_page': page
        })

@app.route('/api/settings', methods=['GET', 'POST'])
def api_settings():
    if request.method == 'POST':
        data = request.json
        for key, value in data.items():
            ConfigSetting.set(key, value)
        return jsonify({'success': True, 'message': 'Settings updated'})
    
    # GET
    settings = {
        'TARGET_URL': ConfigSetting.get('TARGET_URL', ''),
        'PROXY_LIST': ConfigSetting.get('PROXY_LIST', ''),
        'SESSIONS_PER_DAY': ConfigSetting.get('SESSIONS_PER_DAY', '35'),
        'MIN_SESSION_DURATION': ConfigSetting.get('MIN_SESSION_DURATION', '240'),
        'MAX_SESSION_DURATION': ConfigSetting.get('MAX_SESSION_DURATION', '300'),
        'PAGES_PER_SESSION': ConfigSetting.get('PAGES_PER_SESSION', '4'),
        'HEADLESS': ConfigSetting.get('HEADLESS', 'true'),
        'USER_AGENT_ROTATION': ConfigSetting.get('USER_AGENT_ROTATION', 'true')
    }
    return jsonify(settings)

@app.route('/api/run-now', methods=['POST'])
def run_now():
    """Trigger a session immediately"""
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
    """Test if a proxy is working"""
    data = request.json
    proxy = data.get('proxy')
    
    try:
        import requests
        proxies = {
            'http': proxy,
            'https': proxy
        }
        response = requests.get('https://httpbin.org/ip', proxies=proxies, timeout=10)
        return jsonify({
            'success': True,
            'message': 'Proxy is working',
            'response': response.json()
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        })

# Background scheduler
scheduler = BackgroundScheduler()

def scheduled_session():
    with app.app_context():
        monitor.run_session()
        socketio.emit('session_complete', {'timestamp': datetime.utcnow().isoformat()})

def init_scheduler():
    """Initialize the scheduler with random times"""
    scheduler.remove_all_jobs()
    
    sessions_per_day = int(ConfigSetting.get('SESSIONS_PER_DAY', 35))
    
    # Create random schedule
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

@app.before_request
def check_scheduler():
    # Ensure scheduler is running
    if not scheduler.running:
        init_scheduler()

if __name__ == '__main__':
    create_tables()
    # BUG FIX #2: Wrapped init_scheduler in app_context
    with app.app_context():
        init_scheduler()
    socketio.run(app, host='0.0.0.0', port=Config.DASHBOARD_PORT, debug=True)
else:
    create_tables()
    # BUG FIX #2: Wrapped init_scheduler in app_context
    with app.app_context():
        init_scheduler()
