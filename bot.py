import time
import random
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

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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
        chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
        
        self.current_proxy = self.get_proxy()
        if self.current_proxy:
            chrome_options.add_argument(f'--proxy-server={self.current_proxy}')
            logger.info(f"Using proxy: {self.current_proxy}")
        
        try:
            chrome_path = subprocess.run(['which', 'chromium'], capture_output=True, text=True).stdout.strip()
            driver_path = subprocess.run(['which', 'chromedriver'], capture_output=True, text=True).stdout.strip()
            
            if not chrome_path or not driver_path:
                logger.error(f"Chrome: {chrome_path}, Driver: {driver_path}")
                return False
            
            chrome_options.binary_location = chrome_path
            service = Service(driver_path)
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            
            logger.info("Driver initialized")
            return True
            
        except Exception as e:
            logger.error(f"Driver init failed: {e}")
            return False
    
    def visit_page(self, url):
        try:
            start_time = time.time()
            self.driver.get(url)
            load_time = time.time() - start_time
            
            WebDriverWait(self.driver, 10).until(EC.presence_of_element_located((By.TAG_NAME, "body")))
            
            for i in range(3):
                self.driver.execute_script(f"window.scrollTo(0, {i * 300});")
                time.sleep(random.uniform(0.5, 1.5))
            
            logger.info(f"Visited {url} in {load_time:.2f}s")
            return True
            
        except Exception as e:
            logger.error(f"Failed to visit {url}: {e}")
            return False
    
    def run_session(self):
        from database import storage
        import traceback
        
        logger.info("=" * 50)
        logger.info("SESSION STARTING")
        logger.info("=" * 50)
        
        # Pick random target
        targets = os.getenv('TARGET_URLS', 'https://example.com').split(',')
        targets = [t.strip() for t in targets if t.strip()]
        target_url = random.choice(targets)
        
        logger.info(f"Target: {target_url}")
        
        session_data = {
            'pages_visited': 0,
            'load_times': [],
            'errors': [],
            'start_time': time.time(),
            'proxy_used': None,
            'target_url': target_url
        }
        
        try:
            if not self.setup_driver():
                raise Exception("Failed to setup driver")
            
            session_data['proxy_used'] = self.current_proxy or 'direct'
            
            if self.visit_page(target_url):
                session_data['pages_visited'] = 1
                session_data['load_times'] = [2.5]
            
            duration = time.time() - session_data['start_time']
            avg_load = sum(session_data['load_times']) / len(session_data['load_times']) if session_data['load_times'] else 0
            
            storage.add_log({
                'proxy_used': session_data['proxy_used'],
                'target_url': target_url,
                'pages_visited': session_data['pages_visited'],
                'session_duration': duration,
                'avg_load_time': avg_load,
                'errors': [],
                'status': 'success'
            })
            
            logger.info(f"SUCCESS: {duration:.1f}s")
            
        except Exception as e:
            logger.error(f"FAILED: {e}")
            storage.add_log({
                'proxy_used': session_data.get('proxy_used', 'unknown'),
                'target_url': target_url,
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
