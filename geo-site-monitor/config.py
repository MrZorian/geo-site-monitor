import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.getenv('SECRET_KEY', 'your-secret-key-change-this')
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL', 'sqlite:///monitor.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Bot Configuration
    TARGET_URL = os.getenv('TARGET_URL', 'https://example.com')
    PROXY_LIST = os.getenv('PROXY_LIST', '').split(',') if os.getenv('PROXY_LIST') else []
    SESSIONS_PER_DAY = int(os.getenv('SESSIONS_PER_DAY', 35))
    MIN_SESSION_DURATION = int(os.getenv('MIN_SESSION_DURATION', 240))  # 4 minutes
    MAX_SESSION_DURATION = int(os.getenv('MAX_SESSION_DURATION', 300))  # 5 minutes
    PAGES_PER_SESSION = int(os.getenv('PAGES_PER_SESSION', 4))
    
    # Browser Configuration
    HEADLESS = os.getenv('HEADLESS', 'true').lower() == 'true'
    USER_AGENT_ROTATION = os.getenv('USER_AGENT_ROTATION', 'true').lower() == 'true'
    
    # Dashboard
    DASHBOARD_PORT = int(os.getenv('PORT', 5000))