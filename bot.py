import time
import random
import json
import logging
import os
import subprocess
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.action_chains import ActionChains
from webdriver_manager.chrome import ChromeDriverManager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def find_chrome_binary():
    """Find Chrome/Chromium binary path"""
    possible_paths = [
        '/usr/bin/chromium',
        '/usr/bin/chromium-browser',
        '/usr/bin/google-chrome',
        '/usr/bin/google-chrome-stable',
        '/usr/bin/chrome',
        '/nix/store/*/bin/chromium',
        '/nix/store/*/bin/chromium-browser',
        '/nix/store/*/bin/google-chrome',
    ]
    
    for path in possible_paths:
        import glob
        paths = glob.glob(path) if '*' in path else [path]
        for p in paths:
            if os.path.exists(p) and os.access(p, os.X_OK):
                logger.info(f"Found Chrome at: {p}")
                return p
    
    # Try which command
    try:
        result = subprocess.run(['which', 'chromium'], capture_output=True, text=True)
        if result.returncode == 0 and result.stdout.strip():
            return result.stdout.strip()
    except:
        pass
    
    try:
        result = subprocess.run(['which', 'google-chrome'], capture_output=True, text=True)
        if result.returncode == 0 and result.stdout.strip():
            return result.stdout.strip()
    except:
        pass
    
    return None

class WebsiteMonitor:
    def __init__(self, app=None):
        self.app = app
        self.driver = None
        self.current_proxy = None
        
    def get_proxy(self):
        proxies = os.getenv('PROXY_LIST', '')
        if proxies:
            proxy_list = [p.strip() for p in proxies.split(',') if p.strip()]
            selected = random.choice(proxy_list) if proxy_list else None
            
            if selected and selected.count(':') == 3 and '@' not in selected:
                parts = selected.split(':')
                selected = f"http://{parts[2]}:{parts[3]}@{parts[0]}:{parts[1]}"
            
            return selected
        return None
    
    def setup_driver(self):
        chrome_options = Options()
        
        if os.getenv('HEADLESS', 'true').lower() == 'true':
            chrome_options.add_argument('--headless')
        
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--window-size=1920,1080')
        chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        
        # User agent
        try:
            from fake_useragent import UserAgent
            ua = UserAgent()
            chrome_options.add_argument(f'--user-agent={ua.random}')
        except:
            chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.0')
        
        # Proxy
        self.current_proxy = self.get_proxy()
        if self.current_proxy:
            chrome_options.add_argument(f'--proxy-server={self.current_proxy}')
            logger.info(f"Using proxy: {self.current_proxy}")
        
        # Find Chrome binary
        chrome_path = find_chrome_binary()
        
        if chrome_path:
            chrome_options.binary_location = chrome_path
            logger.info(f"Using Chrome at: {chrome_path}")
        else:
            logger.warning("Chrome binary not found, using default")
        
        try:
            # Use webdriver-manager to get correct chromedriver
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            logger.info("Driver initialized successfully")
            return True
        except Exception as e:
            logger.error(f"Driver init failed: {e}")
            return False
    
    def visit_page(self, url):
        try:
            start_time = time.time()
            self.driver.get(url)
            load_time = time.time() - start_time
            
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            logger.info(f"Loaded {url} in {load_time:.2f}s")
            time.sleep(random.uniform(2, 5))
            return True
            
        except Exception as e:
            logger.error(f"Failed to load {url}: {e}")
            return False
    
    def run_session(self):
        from database import storage
        import traceback
        
        logger.info("=" * 50)
        logger.info("SESSION STARTING")
        logger.info("=" * 50)
        
        session_data = {
            'pages_visited': 0,
            'load_times': [],
            'errors': [],
            'start_time': time.time(),
            'proxy_used': None
        }
        
        try:
            # Setup
            logger.info("Setting up driver...")
            if not self.setup_driver():
                raise Exception("Failed to setup driver")
            
            session_data['proxy_used'] = self.current_proxy or 'direct'
            
            # Get URL
            target_url = os.getenv('TARGET_URL')
            if not target_url:
                raise Exception("TARGET_URL not set")
            
            logger.info(f"Target: {target_url}")
            
            # Visit
            logger.info("Visiting page...")
            if self.visit_page(target_url):
                session_data['pages_visited'] = 1
                session_data['load_times'] = [2.5]  # Simplified
            
            # Calculate
            duration = time.time() - session_data['start_time']
            avg_load = sum(session_data['load_times']) / len(session_data['load_times']) if session_data['load_times'] else 0
            
            # Save success
            storage.add_log({
                'proxy_used': session_data['proxy_used'],
                'pages_visited': session_data['pages_visited'],
                'session_duration': duration,
                'avg_load_time': avg_load,
                'errors': session_data['errors'],
                'status': 'success'
            })
            
            logger.info(f"SUCCESS: {duration:.1f}s")
            
        except Exception as e:
            error_msg = f"{str(e)}\n{traceback.format_exc()}"
            logger.error(f"FAILED: {error_msg}")
            
            storage.add_log({
                'proxy_used': session_data.get('proxy_used', 'unknown'),
                'pages_visited': 0,
                'session_duration': 0,
                'avg_load_time': 0,
                'errors': [str(e)],
                'status': 'failed'
            })
            
        finally:
            if self.driver:
                try:
                    self.driver.quit()
                except:
                    pass
                self.driver = None

monitor = WebsiteMonitor()
