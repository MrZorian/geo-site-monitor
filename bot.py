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
        except:
            pass
    
    def click_ad_by_coordinates(self):
        """Click specific coordinates where Social Crave ad appears"""
        try:
            logger.info("=== CLICKING AD BY COORDINATES ===")
            
            # The ad appears in top-right corner
            # For 1920x1080 screen, try these coordinates:
            possible_coords = [
                (1700, 150),   # Top right area
                (1650, 100),   # Slightly left
                (1750, 200),   # Lower
                (1600, 80),    # More left
                (1800, 100),   # Far right
                (1720, 120),   # Center of notification
            ]
            
            for x, y in possible_coords:
                logger.info(f"Trying coordinates: x={x}, y={y}")
                
                # Use ActionChains to move and click
                try:
                    action = ActionChains(self.driver)
                    action.move_by_offset(x, y)
                    action.pause(0.5)
                    action.click()
                    action.perform()
                    
                    logger.info(f"Clicked at {x},{y}")
                    time.sleep(3)
                    
                    # Check if new tab opened
                    if len(self.driver.window_handles) > 1:
                        logger.info("SUCCESS! New tab opened from coordinate click!")
                        return True
                        
                    # Reset mouse position
                    action = ActionChains(self.driver)
                    action.move_by_offset(-x, -y)
                    action.perform()
                    
                except Exception as e:
                    logger.warning(f"Coordinate click failed: {e}")
                    continue
            
            # JavaScript click at coordinates
            logger.info("Trying JavaScript coordinate click...")
            try:
                self.driver.execute_script("""
                    // Try multiple positions in top-right quadrant
                    var positions = [
                        {x: window.innerWidth - 150, y: 100},
                        {x: window.innerWidth - 200, y: 150},
                        {x: window.innerWidth - 100, y: 80},
                        {x: window.innerWidth - 250, y: 120}
                    ];
                    
                    for (var i = 0; i < positions.length; i++) {
                        var el = document.elementFromPoint(positions[i].x, positions[i].y);
                        if (el) {
                            console.log('Clicking element at', positions[i].x, positions[i].y, el.tagName);
                            el.click();
                            return 'clicked';
                        }
                    }
                    return 'none';
                """)
                
                time.sleep(3)
                
                if len(self.driver.window_handles) > 1:
                    logger.info("JavaScript coordinate click worked!")
                    return True
                    
            except Exception as e:
                logger.warning(f"JS coordinate click failed: {e}")
            
            return False
            
        except Exception as e:
            logger.error(f"Coordinate click error: {e}")
            return False
    
    def find_iframe_ads(self):
        """Look for ads inside iframes"""
        try:
            logger.info("=== CHECKING IFRAMES FOR ADS ===")
            
            # Find all iframes
            iframes = self.driver.find_elements(By.TAG_NAME, "iframe")
            logger.info(f"Found {len(iframes)} iframes")
            
            for i, iframe in enumerate(iframes):
                try:
                    # Check iframe size (ads are usually small)
                    size = iframe.size
                    logger.info(f"Iframe {i}: size {size}")
                    
                    if size['width'] > 100 and size['height'] > 50:
                        # Switch to iframe
                        self.driver.switch_to.frame(iframe)
                        logger.info(f"Switched to iframe {i}")
                        
                        # Look for clickables inside
                        try:
                            clickables = self.driver.find_elements(By.XPATH, "//*[contains(text(), 'Click') or contains(text(), 'click') or @onclick or @href]")
                            logger.info(f"Found {len(clickables)} clickable elements in iframe")
                            
                            if clickables:
                                # Click first one
                                clickables[0].click()
                                logger.info("Clicked inside iframe!")
                                
                                # Switch back
                                self.driver.switch_to.default_content()
                                return True
                                
                        except Exception as e:
                            logger.warning(f"Error inside iframe: {e}")
                        
                        # Switch back
                        self.driver.switch_to.default_content()
                        
                except Exception as e:
                    logger.warning(f"Iframe {i} error: {e}")
                    try:
                        self.driver.switch_to.default_content()
                    except:
                        pass
            
            return False
            
        except Exception as e:
            logger.error(f"Iframe search error: {e}")
            try:
                self.driver.switch_to.default_content()
            except:
                pass
            return False
    
    def aggressive_ad_click(self):
        """AGGRESSIVE: Click anything in top-right area"""
        try:
            logger.info("=== AGGRESSIVE AD CLICKING ===")
            
            # Scroll to top first
            self.driver.execute_script("window.scrollTo(0, 0);")
            time.sleep(2)
            
            # Try to find ANY clickable element in top-right
            try:
                # Get all elements
                all_elements = self.driver.find_elements(By.XPATH, "//*")
                logger.info(f"Total elements on page: {len(all_elements)}")
                
                for el in all_elements:
                    try:
                        # Check if in top-right area
                        location = el.location
                        size = el.size
                        
                        # Top-right quadrant (x > 1200, y < 300 for 1920 width)
                        if location['x'] > 1200 and location['y'] < 300:
                            if size['width'] > 50 and size['height'] > 30:
                                if el.is_displayed() and el.is_enabled():
                                    # Check if clickable
                                    tag = el.tag_name.lower()
                                    if tag in ['a', 'button', 'div', 'span', 'img', 'ins']:
                                        text = (el.text or '')[:30]
                                        logger.info(f"Found element in top-right: {tag} - '{text}' at ({location['x']}, {location['y']})")
                                        
                                        # Click it!
                                        try:
                                            el.click()
                                            logger.info("CLICKED!")
                                            time.sleep(3)
                                            
                                            if len(self.driver.window_handles) > 1:
                                                logger.info("New tab opened!")
                                                return True
                                        except:
                                            pass
                    except:
                        continue
                        
            except Exception as e:
                logger.error(f"Aggressive search error: {e}")
            
            return False
            
        except Exception as e:
            logger.error(f"Aggressive ad click error: {e}")
            return False
    
    def handle_ad_result(self):
        """Handle after clicking"""
        try:
            time.sleep(4)
            current_handles = self.driver.window_handles
            
            if len(current_handles) > 1:
                new_window = [h for h in current_handles if h != self.main_window][0]
                self.driver.switch_to.window(new_window)
                logger.info("In ad tab")
                
                scroll_time = random.randint(30, 40)
                logger.info(f"Scrolling {scroll_time}s...")
                self.human_like_scroll(scroll_time)
                
                self.driver.close()
                self.driver.switch_to.window(self.main_window)
                logger.info("Returned")
                return True
            else:
                logger.info("Same tab")
                scroll_time = random.randint(30, 40)
                self.human_like_scroll(scroll_time)
                try:
                    self.driver.back()
                    time.sleep(2)
                except:
                    pass
                return True
        except Exception as e:
            logger.error(f"Handle error: {e}")
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
            
            # PAGE 1: Main
            logger.info("=== PAGE 1: Main Page ===")
            self.driver.get(target_url)
            time.sleep(8)  # Wait for ads to load
            self.human_like_scroll(5)
            session_data['pages_visited'] += 1
            
            # METHOD 1: Coordinate clicking
            logger.info("=== METHOD 1: Coordinate Click ===")
            if self.click_ad_by_coordinates():
                if self.handle_ad_result():
                    session_data['ads_clicked'] += 1
                    session_data['pages_visited'] += 1
            
            # METHOD 2: Iframe ads
            if session_data['ads_clicked'] == 0:
                logger.info("=== METHOD 2: Iframe Ads ===")
                if self.find_iframe_ads():
                    if self.handle_ad_result():
                        session_data['ads_clicked'] += 1
                        session_data['pages_visited'] += 1
            
            # METHOD 3: Aggressive clicking
            if session_data['ads_clicked'] == 0:
                logger.info("=== METHOD 3: Aggressive Click ===")
                if self.aggressive_ad_click():
                    if self.handle_ad_result():
                        session_data['ads_clicked'] += 1
                        session_data['pages_visited'] += 1
            
            # Ensure 4-5 min
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
