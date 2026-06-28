import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-key-123')
    
    TARGET_URL = os.getenv('TARGET_URL', 'https://example.com')
    PROXY_LIST = os.getenv('PROXY_LIST', '').split(',') if os.getenv('PROXY_LIST') else []
    SESSIONS_PER_DAY = int(os.getenv('SESSIONS_PER_DAY', 35))
    MIN_SESSION_DURATION = int(os.getenv('MIN_SESSION_DURATION', 240))
    MAX_SESSION_DURATION = int(os.getenv('MAX_SESSION_DURATION', 300))
    PAGES_PER_SESSION = int(os.getenv('PAGES_PER_SESSION', 4))
    
    HEADLESS = os.getenv('HEADLESS', 'true').lower() == 'true'
    USER_AGENT_ROTATION = os.getenv('USER_AGENT_ROTATION', 'true').lower() == 'true'
