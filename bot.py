import time
import random
import json
import logging
from datetime import datetime, timedelta
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.action_chains import ActionChains
from fake_useragent import UserAgent
from database import storage
import requests

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class WebsiteMonitor:
    def __init__(self, app=None):
        self.app = app
        self.driver = None
        self.current_proxy = None
        self.session_data = {
            'pages_visited': 0,
            'load_times': [],
            'errors': [],
            'start_time': None,
            'proxy_used': None,
            'status': 'running'
        }
        
    def get_proxy(self):
        """Get a random proxy from the list"""
        import os
        proxies = os.getenv('PROXY_LIST', '')
        if proxies:
            proxy_list = [p.strip() for p in proxies.split(',') if p.strip()]
            selected = random.choice(proxy_list) if proxy_list else None
            
            # Auto-convert host:port:user:pass to http://user:pass@host:port
            if selected and selected.count(':') == 3 and '@' not in selected:
                parts = selected.split(':')
                selected = f"http://{parts[2]}:{parts[3]}@{parts[0]}:{parts[1]}"
            
            return selected
        return None
    
    def setup_driver(self):
        """Initialize Chrome driver with proxy and user agent"""
        chrome_options = Options()
        
        # Headless mode
        import os
        if os.getenv('HEADLESS', 'true').lower() == 'true':
            chrome_options.add_argument('--headless')
        
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--window-size=1920,1080')
        
        # User agent rotation
        if os.getenv('USER_AGENT_ROTATION', 'true').lower() == 'true':
            try:
                ua = UserAgent()
                chrome_options.add_argument(f'--user-agent={ua.random}')
            except:
                pass
        
        # Proxy setup
        self.current_proxy = self.get_proxy()
        if self.current_proxy:
            chrome_options.add_argument(f'--proxy-server={self.current_proxy}')
            logger.info(f"Using proxy: {self.current_proxy}")
        
        # Additional options for stability
        chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        
        try:
            self.driver = webdriver.Chrome(options=chrome_options)
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            logger.info("Driver initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize driver: {e}")
            raise
    
    def human_like_scroll(self):
        """Simulate human-like scrolling"""
        try:
            total_height = self.driver.execute_script("return document.body.scrollHeight")
            current_position = 0
            scroll_step = random.randint(100, 300)
            
            while current_position < total_height:
                current_position += scroll_step
                self.driver.execute_script(f"window.scrollTo(0, {current_position});")
                time.sleep(random.uniform(0.5, 2))
                
                if random.random() < 0.3:
                    time.sleep(random.uniform(2, 5))
                    
        except Exception as e:
            logger.warning(f"Scroll error: {e}")
    
    def click_random_element(self):
        """Click on random interactive elements"""
        try:
            elements = self.driver.find_elements(By.CSS_SELECTOR, 
                "a[href], button, .btn, [role='button'], nav a")
            
            internal_links = [e for e in elements if self.is_internal_link(e)]
            
            if internal_links and random.random() < 0.7:
                element = random.choice(internal_links)
                try:
                    self.driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", element)
                    time.sleep(random.uniform(1, 3))
                    
                    ActionChains(self.driver).move_to_element(element).pause(random.uniform(0.5, 1.5)).click().perform()
                    logger.info(f"Clicked element: {element.get_attribute('href') or 'button'}")
                    time.sleep(random.uniform(3, 6))
                    return True
                except Exception as e:
                    logger.warning(f"Click failed: {e}")
            return False
        except Exception as e:
            logger.warning(f"Element interaction error: {e}")
            return False
    
    def is_internal_link(self, element):
        """Check if link is internal to the target domain"""
        try:
            href = element.get_attribute('href')
            if not href:
                return False
            import os
            target_domain = os.getenv('TARGET_URL', 'https://example.com')
            return target_domain in href or href.startswith('/')
        except:
            return False
    
    def visit_page(self, url):
        """Visit a page and collect metrics"""
        try:
            start_time = time.time()
            self.driver.get(url)
            load_time = time.time() - start_time
            
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            self.session_data['load_times'].append(load_time)
            self.session_data['pages_visited'] += 1
            
            logger.info(f"Visited {url} in {load_time:.2f}s")
            
            self.human_like_scroll()
            
            if random.random() < 0.6:
                self.click_random_element()
            
            time.sleep(random.uniform(10, 30))
            
            return True
            
        except Exception as e:
            error_msg = f"Error visiting {url}: {str(e)}"
            logger.error(error_msg)
            self.session_data['errors'].append(error_msg)
            return False
    
    def run_session(self):
        """Execute a full monitoring session"""
        import os
        
        # Reset session data
        self.session_data = {
            'pages_visited': 0,
            'load_times': [],
            'errors': [],
            'start_time': time.time(),
            'proxy_used': None,
            'status': 'running'
        }
        
        try:
            self.setup_driver()
            self.session_data['proxy_used'] = self.current_proxy or 'direct'
            
            target_url = os.getenv('TARGET_URL', 'https://example.com')
            pages_to_visit = int(os.getenv('PAGES_PER_SESSION', 4))
            min_duration = int(os.getenv('MIN_SESSION_DURATION', 240))
            max_duration = int(os.getenv('MAX_SESSION_DURATION', 300))
            
            # Visit main page
            self.visit_page(target_url)
            
            # Visit additional pages
            visited_urls = {target_url}
            for _ in range(pages_to_visit - 1):
                links = self.driver.find_elements(By.CSS_SELECTOR, "a[href]")
                internal_links = []
                for link in links:
                    href = link.get_attribute('href')
                    if href and target_url in href and href not in visited_urls:
                        internal_links.append(href)
                
                if internal_links:
                    next_url = random.choice(internal_links[:5])
                    visited_urls.add(next_url)
                    self.visit_page(next_url)
                else:
                    break
            
            # Ensure minimum session duration
            elapsed = time.time() - self.session_data['start_time']
            if elapsed < min_duration:
                time.sleep(min_duration - elapsed)
            
            # Calculate metrics
            session_duration = time.time() - self.session_data['start_time']
            avg_load = sum(self.session_data['load_times']) / len(self.session_data['load_times']) if self.session_data['load_times'] else 0
            
            # Save to memory storage
            storage.add_log({
                'proxy_used': self.session_data['proxy_used'],
                'pages_visited': self.session_data['pages_visited'],
                'session_duration': session_duration,
                'avg_load_time': avg_load,
                'errors': self.session_data['errors'],
                'status': 'success' if not self.session_data['errors'] else 'completed_with_errors'
            })
            
            logger.info(f"Session completed: {session_duration:.2f}s, {self.session_data['pages_visited']} pages")
            
        except Exception as e:
            logger.error(f"Session failed: {e}")
            storage.add_log({
                'proxy_used': self.current_proxy or 'direct',
                'pages_visited': self.session_data['pages_visited'],
                'session_duration': 0,
                'avg_load_time': 0,
                'errors': [str(e)],
                'status': 'failed'
            })
            
        finally:
            if self.driver:
                self.driver.quit()
                self.driver = None
