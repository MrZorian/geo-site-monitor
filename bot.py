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
from selenium.webdriver.common.action_chains import ActionChains

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class WebsiteMonitor:
    def __init__(self, app=None):
        self.app = app
        self.driver = None
        self.current_proxy = None
        self.main_window = None
        
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
    
    def get_target_urls(self):
        urls = os.getenv('TARGET_URLS', '')
        if not urls:
            from database import ConfigSetting
            urls = ConfigSetting.get('TARGET_URLS', 'https://example.com')
        url_list = [u.strip() for u in urls.split(',') if u.strip()]
        real_urls = [u for u in url_list if 'example.com' not in u]
        return real_urls if real_urls else url_list
    
    def setup_driver(self):
        chrome_options = Options()
        if os.getenv('HEADLESS', 'true').lower() == 'true':
            chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--window-size=1920,1080')
        chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        chrome_options.add_argument('--single-process')
        chrome_options.add_argument('--no-zygote')
        chrome_options.add_argument('--disable-setuid-sandbox')
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation", "enable-popup-blocking"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
        
        self.current_proxy = self.get_proxy()
        if self.current_proxy:
            chrome_options.add_argument(f'--proxy-server={self.current_proxy}')
        
        try:
            chrome_path = subprocess.run(['which', 'chromium'], capture_output=True, text=True).stdout.strip()
            driver_path = subprocess.run(['which', 'chromedriver'], capture_output=True, text=True).stdout.strip()
            if not chrome_path or not driver_path:
                return False
            chrome_options.binary_location = chrome_path
            service = Service(driver_path)
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            self.driver.set_page_load_timeout(30)
            self.main_window = self.driver.current_window_handle
            logger.info("Driver initialized")
            return True
        except Exception as e:
            logger.error(f"Driver init failed: {e}")
            return False
    
    def human_like_scroll(self, duration=20):
        try:
            start = time.time()
            while time.time() - start < duration:
                scroll_pixels = random.randint(200, 800)
                scroll_direction = random.choice([1, -1])
                self.driver.execute_script(f"window.scrollBy(0, {scroll_pixels * scroll_direction});")
                time.sleep(random.uniform(1, 4))
                if random.random() < 0.25:
                    self.driver.execute_script(f"window.scrollBy(0, -{random.randint(100, 300)});")
                    time.sleep(random.uniform(2, 5))
        except Exception as e:
            pass
    
    def find_social_crave_ad(self):
        """SPECIFIC for Social Crave website - Top right notification ad"""
        try:
            logger.info("=== LOOKING FOR SOCIAL CRAVE NOTIFICATION AD ===")
            
            # Wait for ad to appear
            time.sleep(8)
            
            # METHOD 1: Find by exact text "Click Here" near "Hide"
            try:
                # Look for elements containing "Click Here"
                elements = self.driver.find_elements(By.XPATH, "//*[contains(text(), 'Click Here')]")
                logger.info(f"Found {len(elements)} elements with 'Click Here' text")
                
                for el in elements:
                    try:
                        if el.is_displayed():
                            # Check if parent or nearby element has "Hide" (indicates notification)
                            parent = el.find_element(By.XPATH, "..")
                            grandparent = parent.find_element(By.XPATH, "..")
                            
                            # Get parent HTML to check
                            parent_html = parent.get_attribute('innerHTML') or ''
                            grandparent_html = grandparent.get_attribute('innerHTML') or ''
                            
                            if 'Hide' in parent_html or 'Hide' in grandparent_html or 'FB' in parent_html or 'Facebook' in parent_html:
                                logger.info("Found Social Crave notification ad with 'Click Here'!")
                                
                                # Scroll to it (though it's fixed position)
                                self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", el)
                                time.sleep(2)
                                
                                # Hover
                                ActionChains(self.driver).move_to_element(el).pause(0.5).perform()
                                
                                # CLICK
                                logger.info("CLICKING the 'Click Here' button!")
                                try:
                                    el.click()
                                except:
                                    parent.click()
                                
                                return True
                    except:
                        continue
            except Exception as e:
                logger.warning(f"Text search failed: {e}")
            
            # METHOD 2: Find by CSS - notification style in top right
            notification_selectors = [
                # Top right positioned elements
                "[style*='top: 0'][style*='right: 0']",
                "[style*='top:0'][style*='right:0']",
                "[style*='position: fixed'][style*='top:']",
                "[style*='position:fixed'][style*='top:']",
                "[style*='z-index: 999']",
                "[style*='z-index: 1000']",
                "[style*='z-index: 9999']",
                
                # Common notification classes
                ".notification",
                ".toast",
                ".alert",
                ".popup",
                ".modal",
                "[class*='notification']",
                "[class*='toast']",
                "[class*='alert']",
                "[class*='popup']",
                
                # Elements with red badge (the "1" badge)
                "[class*='badge']",
                "[class*='unread']",
            ]
            
            for selector in notification_selectors:
                try:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    logger.info(f"Selector '{selector[:40]}' found {len(elements)} elements")
                    
                    for el in elements:
                        try:
                            if el.is_displayed():
                                size = el.size
                                if size['width'] > 200 and size['height'] > 50:
                                    # Check if it contains "Click Here" text
                                    text = el.text or ''
                                    if 'Click Here' in text or 'click here' in text.lower():
                                        logger.info(f"Found notification with Click Here: {size}")
                                        
                                        # Find the Click Here button inside
                                        buttons = el.find_elements(By.XPATH, ".//*[contains(text(), 'Click Here')]")
                                        if buttons:
                                            logger.info("CLICKING notification button!")
                                            buttons[0].click()
                                            return True
                                        else:
                                            # Click the whole element
                                            el.click()
                                            return True
                        except:
                            continue
                except:
                    continue
            
            # METHOD 3: JavaScript - find element by position (top right area)
            logger.info("Trying JavaScript coordinate method...")
            try:
                # Click on top right area where notification usually is
                # Coordinates around x=1700, y=100 for 1920x1080 screen
                logger.info("Clicking top-right area where notification appears...")
                
                # Use JavaScript to click at coordinates
                self.driver.execute_script("""
                    var element = document.elementFromPoint(window.innerWidth - 200, 100);
                    if (element) {
                        element.click();
                        return 'Clicked: ' + element.tagName;
                    }
                    return 'No element found';
                """)
                
                time.sleep(2)
                
                # Check if new tab opened
                if len(self.driver.window_handles) > 1:
                    logger.info("New tab opened from coordinate click!")
                    return True
                    
            except Exception as e:
                logger.warning(f"Coordinate click failed: {e}")
            
            # METHOD 4: Screenshot for debugging
            try:
                screenshot = self.driver.get_screenshot_as_base64()
                logger.info(f"Screenshot taken for debugging (length: {len(screenshot)})")
            except:
                pass
            
            logger.info("No Social Crave ad found")
            return False
            
        except Exception as e:
            logger.error(f"Social Crave ad find error: {e}")
            return False
    
    def handle_ad_click(self):
        """Handle ad click result"""
        try:
            time.sleep(4)
            current_handles = self.driver.window_handles
            
            if len(current_handles) > 1:
                new_window = [h for h in current_handles if h != self.main_window][0]
                self.driver.switch_to.window(new_window)
                logger.info("Switched to ad tab")
                
                scroll_time = random.randint(30, 40)
                logger.info(f"Scrolling ad for {scroll_time}s...")
                self.human_like_scroll(scroll_time)
                
                self.driver.close()
                self.driver.switch_to.window(self.main_window)
                logger.info("Returned to main")
                return True
            else:
                logger.info("Ad in same tab")
                scroll_time = random.randint(30, 40)
                self.human_like_scroll(scroll_time)
                try:
                    self.driver.back()
                    time.sleep(2)
                except:
                    pass
                return True
        except Exception as e:
            logger.error(f"Handle ad error: {e}")
            return False
    
    def click_navigation_link(self, target_domain):
        try:
            nav_keywords = ['about', 'contact', 'services', 'products', 'blog', 'news']
            links = self.driver.find_elements(By.TAG_NAME, "a")
            nav_links = []
            for link in links:
                try:
                    text = link.text.lower().strip()
                    href = link.get_attribute('href') or ''
                    if any(k in text for k in nav_keywords):
                        if target_domain in href or href.startswith('/'):
                            nav_links.append(link)
                except:
                    continue
            if nav_links:
                link = random.choice(nav_links)
                self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", link)
                time.sleep(2)
                link.click()
                time.sleep(random.uniform(4, 8))
                self.human_like_scroll(random.randint(15, 25))
                return True
        except:
            pass
        return False
    
    def run_session(self):
        from database import storage
        targets = self.get_target_urls()
        if not targets:
            logger.error("No targets!")
            return
        
        target_url = random.choice(targets)
        logger.info(f"SESSION START: {target_url}")
        
        session_data = {
            'pages_visited': 0,
            'ads_clicked': 0,
            'start_time': time.time(),
            'proxy_used': None,
            'target_url': target_url
        }
        
        try:
            if not self.setup_driver():
                raise Exception("Driver failed")
            
            session_data['proxy_used'] = self.current_proxy or 'direct'
            
            # PAGE 1: Main page
            logger.info("=== PAGE 1: Main Page ===")
            self.driver.get(target_url)
            time.sleep(5)
            self.human_like_scroll(10)
            session_data['pages_visited'] += 1
            
            # TRY MULTIPLE TIMES TO FIND AD
            for attempt in range(3):
                logger.info(f"=== AD ATTEMPT {attempt + 1} ===")
                if self.find_social_crave_ad():
                    if self.handle_ad_click():
                        session_data['ads_clicked'] += 1
                        session_data['pages_visited'] += 1
                        logger.info(f"AD CLICKED! Total: {session_data['ads_clicked']}")
                        break
                time.sleep(3)
            
            # Navigation pages
            for i in range(3):
                if self.click_navigation_link(target_url.split('/')[2]):
                    session_data['pages_visited'] += 1
                    time.sleep(5)
                    # Try ad on this page too
                    if self.find_social_crave_ad():
                        if self.handle_ad_click():
                            session_data['ads_clicked'] += 1
                            session_data['pages_visited'] += 1
            
            # Ensure 4-5 min duration
            elapsed = time.time() - session_data['start_time']
            target_duration = random.randint(240, 300)
            if elapsed < target_duration:
                wait_time = target_duration - elapsed
                logger.info(f"Waiting {wait_time:.0f}s...")
                time.sleep(wait_time)
            
            total_duration = time.time() - session_data['start_time']
            
            storage.add_log({
                'proxy_used': session_data['proxy_used'],
                'target_url': target_url,
                'pages_visited': session_data['pages_visited'],
                'ads_clicked': session_data['ads_clicked'],
                'session_duration': total_duration,
                'avg_load_time': 2.5,
                'errors': [],
                'status': 'success'
            })
            
            logger.info(f"COMPLETE: {total_duration:.0f}s, {session_data['pages_visited']} pages, {session_data['ads_clicked']} ads")
            
        except Exception as e:
            logger.error(f"FAILED: {e}")
            storage.add_log({
                'proxy_used': session_data.get('proxy_used', 'unknown'),
                'target_url': target_url,
                'pages_visited': session_data['pages_visited'],
                'ads_clicked': session_data['ads_clicked'],
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
                self.main_window = None

monitor = WebsiteMonitor()
