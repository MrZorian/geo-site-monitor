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
from selenium.webdriver.common.action_chains import ActionChains

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class WebsiteMonitor:
    def __init__(self, app=None):
        self.app = app
        self.driver = None
        self.current_proxy = None
        self.visited_urls = set()
        
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
        """Get list of target URLs from settings"""
        urls = os.getenv('TARGET_URLS', '')
        if not urls or urls == 'https://example.com':
            # Try to get from database if env not set
            from database import ConfigSetting
            urls = ConfigSetting.get('TARGET_URLS', 'https://example.com')
        
        url_list = [u.strip() for u in urls.split(',') if u.strip()]
        # Filter out example.com if user has real URLs
        real_urls = [u for u in url_list if 'example.com' not in u]
        return real_urls if real_urls else url_list
    
    def setup_driver(self):
        """Initialize Chrome driver"""
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
        
        # Random user agent
        user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/119.0'
        ]
        chrome_options.add_argument(f'--user-agent={random.choice(user_agents)}')
        
        # Proxy
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
            
            logger.info("Driver initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Driver init failed: {e}")
            return False
    
    def human_like_scroll(self, duration=10):
        """Scroll like a human for specified duration"""
        try:
            start = time.time()
            while time.time() - start < duration:
                # Random scroll amount
                scroll_pixels = random.randint(100, 500)
                self.driver.execute_script(f"window.scrollBy(0, {scroll_pixels});")
                
                # Random pause between scrolls
                time.sleep(random.uniform(0.5, 3))
                
                # Occasionally scroll back up slightly
                if random.random() < 0.3:
                    self.driver.execute_script(f"window.scrollBy(0, -{random.randint(50, 150)});")
                    time.sleep(random.uniform(1, 2))
                
                # Stop if reached bottom
                scroll_height = self.driver.execute_script("return document.body.scrollHeight")
                current_pos = self.driver.execute_script("return window.pageYOffset + window.innerHeight")
                if current_pos >= scroll_height:
                    break
                    
        except Exception as e:
            logger.warning(f"Scroll error: {e}")
    
    def find_and_click_ad(self):
        """Find and click on an ad"""
        try:
            # Common ad selectors
            ad_selectors = [
                "iframe[src*='googleads']",
                "iframe[src*='doubleclick']",
                "iframe[id*='google_ads']",
                "[data-ad-slot]",
                ".adsbygoogle",
                "a[href*='googleadservices']",
                "a[href*='doubleclick']",
                "ins.adsbygoogle",
                "[class*='advertisement']",
                "[class*='ad-']",
                "a[target='_blank']",  # Often ads open in new tab
                "img[alt*='ad' i]",
                "img[alt*='sponsored' i]"
            ]
            
            ads = []
            for selector in ad_selectors:
                try:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    ads.extend(elements)
                except:
                    continue
            
            # Filter visible ads
            visible_ads = [ad for ad in ads if ad.is_displayed() and ad.size['height'] > 50]
            
            if visible_ads:
                ad = random.choice(visible_ads)
                
                # Scroll to ad
                self.driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", ad)
                time.sleep(random.uniform(2, 4))
                
                # Click ad
                logger.info("Clicking on ad...")
                ActionChains(self.driver).move_to_element(ad).pause(random.uniform(0.5, 1.5)).click().perform()
                
                # Wait for new tab/window
                time.sleep(3)
                
                # Switch to new tab if opened
                original_window = self.driver.current_window_handle
                if len(self.driver.window_handles) > 1:
                    self.driver.switch_to.window(self.driver.window_handles[-1])
                    logger.info("Switched to ad tab")
                
                # Scroll ad page for 30-40 seconds
                scroll_duration = random.randint(30, 40)
                logger.info(f"Scrolling ad page for {scroll_duration}s...")
                self.human_like_scroll(scroll_duration)
                
                # Close ad tab and return
                if len(self.driver.window_handles) > 1:
                    self.driver.close()
                    self.driver.switch_to.window(original_window)
                    logger.info("Returned to main page")
                else:
                    # Go back if no new tab
                    self.driver.back()
                    time.sleep(2)
                
                return True
                
        except Exception as e:
            logger.warning(f"Ad click failed: {e}")
        
        return False
    
    def click_random_link(self, base_domain):
        """Click a random internal link"""
        try:
            # Find all links
            links = self.driver.find_elements(By.CSS_SELECTOR, "a[href]")
            
            internal_links = []
            for link in links:
                try:
                    href = link.get_attribute('href')
                    if href and base_domain in href and href not in self.visited_urls:
                        # Check if visible and clickable
                        if link.is_displayed() and link.size['height'] > 10:
                            internal_links.append(link)
                except:
                    continue
            
            if internal_links:
                # Pick random link from first 10
                link = random.choice(internal_links[:10])
                
                # Scroll to it
                self.driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", link)
                time.sleep(random.uniform(2, 4))
                
                # Click
                href = link.get_attribute('href')
                logger.info(f"Clicking internal link: {href}")
                link.click()
                
                # Wait for load
                time.sleep(random.uniform(3, 6))
                
                # Scroll the new page
                self.human_like_scroll(random.randint(8, 15))
                
                self.visited_urls.add(href)
                return True
                
        except Exception as e:
            logger.warning(f"Link click failed: {e}")
        
        return False
    
    def visit_page(self, url, scroll_time=15):
        """Visit a page with human behavior"""
        try:
            logger.info(f"Visiting: {url}")
            start_time = time.time()
            self.driver.get(url)
            load_time = time.time() - start_time
            
            # Wait for page load
            WebDriverWait(self.driver, 15).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            # Initial scroll
            self.human_like_scroll(scroll_time)
            
            logger.info(f"Page loaded in {load_time:.2f}s, scrolled for {scroll_time}s")
            return True
            
        except Exception as e:
            logger.error(f"Failed to visit {url}: {e}")
            return False
    
    def run_session(self):
        """Run complete session with multiple pages and ad clicking"""
        from database import storage
        import traceback
        
        # Get target URLs (NOT example.com if possible)
        target_urls = self.get_target_urls()
        if not target_urls:
            logger.error("No target URLs configured!")
            return
        
        # Pick random target
        target_url = random.choice(target_urls)
        base_domain = target_url.split('/')[2] if '//' in target_url else target_url
        
        logger.info("=" * 60)
        logger.info(f"SESSION STARTING - Target: {target_url}")
        logger.info("=" * 60)
        
        session_data = {
            'pages_visited': 0,
            'load_times': [],
            'errors': [],
            'start_time': time.time(),
            'proxy_used': None,
            'target_url': target_url,
            'ads_clicked': 0
        }
        
        self.visited_urls = {target_url}
        
        try:
            # Setup driver
            if not self.setup_driver():
                raise Exception("Failed to setup driver")
            
            session_data['proxy_used'] = self.current_proxy or 'direct'
            
            # PAGE 1: Main page
            logger.info("=== PAGE 1: Main Page ===")
            if self.visit_page(target_url, scroll_time=random.randint(10, 20)):
                session_data['pages_visited'] += 1
                
                # Try to click an ad on main page
                if self.find_and_click_ad():
                    session_data['ads_clicked'] += 1
                    session_data['pages_visited'] += 1  # Count ad page as visit
                
                # Click internal link to page 2
                time.sleep(random.uniform(3, 6))
                if self.click_random_link(base_domain):
                    session_data['pages_visited'] += 1
                    
                    # PAGE 2: Try ad on second page
                    time.sleep(random.uniform(5, 10))
                    if random.random() < 0.7:  # 70% chance to click another ad
                        if self.find_and_click_ad():
                            session_data['ads_clicked'] += 1
                            session_data['pages_visited'] += 1
                    
                    # Click to page 3
                    time.sleep(random.uniform(3, 6))
                    if self.click_random_link(base_domain):
                        session_data['pages_visited'] += 1
                        
                        # PAGE 3: More scrolling
                        time.sleep(random.uniform(5, 10))
                        self.human_like_scroll(random.randint(8, 15))
                        
                        # Maybe click to page 4
                        if random.random() < 0.5:  # 50% chance for 4th page
                            time.sleep(random.uniform(3, 6))
                            if self.click_random_link(base_domain):
                                session_data['pages_visited'] += 1
                                time.sleep(random.uniform(5, 10))
                                self.human_like_scroll(random.randint(8, 12))
            
            # Calculate session metrics
            duration = time.time() - session_data['start_time']
            
            # Ensure minimum session time (4-5 minutes)
            min_time = int(os.getenv('MIN_SESSION_DURATION', 240))
            max_time = int(os.getenv('MAX_SESSION_DURATION', 300))
            target_time = random.randint(min_time, max_time)
            
            if duration < target_time:
                remaining = target_time - duration
                logger.info(f"Session too short, waiting {remaining:.0f}s more...")
                time.sleep(remaining)
                duration = time.time() - session_data['start_time']
            
            # Save success
            storage.add_log({
                'proxy_used': session_data['proxy_used'],
                'target_url': target_url,
                'pages_visited': session_data['pages_visited'],
                'session_duration': duration,
                'avg_load_time': duration / max(session_data['pages_visited'], 1),
                'errors': session_data['errors'],
                'status': 'success'
            })
            
            logger.info(f"✓ SESSION COMPLETE: {duration:.0f}s, {session_data['pages_visited']} pages, {session_data['ads_clicked']} ads")
            
        except Exception as e:
            logger.error(f"✗ SESSION FAILED: {e}")
            logger.error(traceback.format_exc())
            
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
