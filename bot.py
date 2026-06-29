import time
import random
import logging
import os
import subprocess
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
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
        """Get random proxy"""
        proxies = os.getenv('PROXY_LIST', '')
        if proxies:
            proxy_list = [p.strip() for p in proxies.split(',') if p.strip()]
            selected = random.choice(proxy_list) if proxy_list else None
            
            if selected and selected.count(':') == 3 and '@' not in selected:
                parts = selected.split(':')
                selected = f"http://{parts[2]}:{parts[3]}@{parts[0]}:{parts[1]}"
            
            return selected
        return None
    
    def get_target_urls(self):
        """Get target URLs"""
        urls = os.getenv('TARGET_URLS', '')
        if not urls:
            from database import ConfigSetting
            urls = ConfigSetting.get('TARGET_URLS', 'https://example.com')
        
        url_list = [u.strip() for u in urls.split(',') if u.strip()]
        real_urls = [u for u in url_list if 'example.com' not in u]
        return real_urls if real_urls else url_list
    
    def setup_driver(self):
        """Initialize Chrome driver - STABLE VERSION"""
        chrome_options = Options()
        
        if os.getenv('HEADLESS', 'true').lower() == 'true':
            chrome_options.add_argument('--headless')
        
        # Critical stability options for Railway
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--window-size=1920,1080')
        chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        chrome_options.add_argument('--single-process')
        chrome_options.add_argument('--no-zygote')
        chrome_options.add_argument('--disable-setuid-sandbox')
        
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        
        # User agent
        chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
        
        # Proxy
        self.current_proxy = self.get_proxy()
        if self.current_proxy:
            chrome_options.add_argument(f'--proxy-server={self.current_proxy}')
            logger.info(f"Using proxy: {self.current_proxy}")
        
        try:
            chrome_path = subprocess.run(['which', 'chromium'], capture_output=True, text=True).stdout.strip()
            driver_path = subprocess.run(['which', 'chromedriver'], capture_output=True, text=True).stdout.strip()
            
            if not chrome_path or not driver_path:
                logger.error(f"Chrome not found: {chrome_path}, {driver_path}")
                return False
            
            chrome_options.binary_location = chrome_path
            service = Service(driver_path)
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            self.driver.set_page_load_timeout(30)
            
            logger.info("Driver initialized")
            return True
            
        except Exception as e:
            logger.error(f"Driver init failed: {e}")
            return False
    
    def human_like_scroll(self, duration=10):
        """Scroll like human"""
        try:
            start = time.time()
            while time.time() - start < duration:
                scroll_pixels = random.randint(100, 500)
                self.driver.execute_script(f"window.scrollBy(0, {scroll_pixels});")
                time.sleep(random.uniform(0.5, 2))
                
                if random.random() < 0.3:
                    self.driver.execute_script(f"window.scrollBy(0, -{random.randint(50, 150)});")
                    time.sleep(random.uniform(1, 2))
                    
        except Exception as e:
            logger.warning(f"Scroll error: {e}")
    
    def run_session(self):
        """Run session - visits multiple pages"""
        from database import storage
        
        targets = self.get_target_urls()
        if not targets:
            logger.error("No targets!")
            return
        
        target_url = random.choice(targets)
        logger.info(f"SESSION START: {target_url}")
        
        session_data = {
            'pages_visited': 0,
            'start_time': time.time(),
            'proxy_used': None,
            'target_url': target_url
        }
        
        try:
            if not self.setup_driver():
                raise Exception("Driver failed")
            
            session_data['proxy_used'] = self.current_proxy or 'direct'
            
            # PAGE 1: Main
            logger.info("Page 1: Main")
            self.driver.get(target_url)
            time.sleep(random.uniform(3, 6))
            self.human_like_scroll(random.randint(8, 15))
            session_data['pages_visited'] += 1
            
            # PAGES 2-4: Click links
            for page_num in range(2, 5):
                try:
                    # Find all links
                    links = self.driver.find_elements(By.TAG_NAME, "a")
                    valid_links = []
                    
                    for link in links:
                        try:
                            href = link.get_attribute('href')
                            if href and link.is_displayed():
                                # Check if internal link
                                if target_url in href or href.startswith('/'):
                                    valid_links.append(link)
                        except:
                            continue
                    
                    if not valid_links:
                        logger.info(f"No more links found")
                        break
                    
                    # Click random link
                    link = random.choice(valid_links[:5])
                    logger.info(f"Page {page_num}: Clicking link...")
                    
                    self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", link)
                    time.sleep(random.uniform(2, 4))
                    link.click()
                    
                    # Wait and scroll
                    time.sleep(random.uniform(5, 10))
                    self.human_like_scroll(random.randint(10, 20))
                    session_data['pages_visited'] += 1
                    
                except Exception as e:
                    logger.warning(f"Page {page_num} failed: {e}")
                    break
            
            # Ensure 4-5 min duration
            elapsed = time.time() - session_data['start_time']
            target_duration = random.randint(240, 300)
            
            if elapsed < target_duration:
                wait_time = target_duration - elapsed
                logger.info(f"Waiting extra {wait_time:.0f}s...")
                time.sleep(wait_time)
            
            total_duration = time.time() - session_data['start_time']
            
            # Save success
            storage.add_log({
                'proxy_used': session_data['proxy_used'],
                'target_url': target_url,
                'pages_visited': session_data['pages_visited'],
                'session_duration': total_duration,
                'avg_load_time': 2.5,
                'errors': [],
                'status': 'success'
            })
            
            logger.info(f"COMPLETE: {total_duration:.0f}s, {session_data['pages_visited']} pages")
            
        except Exception as e:
            logger.error(f"FAILED: {e}")
            storage.add_log({
                'proxy_used': session_data.get('proxy_used', 'unknown'),
                'target_url': target_url,
                'pages_visited': session_data['pages_visited'],
                'session_duration': time.time() - session_data['start_time'],
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
