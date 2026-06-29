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
        """Initialize Chrome driver"""
        chrome_options = Options()
        
        if os.getenv('HEADLESS', 'true').lower() == 'true':
            chrome_options.add_argument('--headless')
        
        # Stability options
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--window-size=1920,1080')
        chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        chrome_options.add_argument('--single-process')
        chrome_options.add_argument('--no-zygote')
        chrome_options.add_argument('--disable-setuid-sandbox')
        
        # IMPORTANT: Allow popups and notifications for ads
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation", "enable-popup-blocking"])
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
                logger.error(f"Chrome not found")
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
        """Scroll like human"""
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
                
                scroll_height = self.driver.execute_script("return document.body.scrollHeight")
                current_pos = self.driver.execute_script("return window.pageYOffset + window.innerHeight")
                
                if current_pos >= scroll_height and (time.time() - start) > duration * 0.6:
                    break
                    
        except Exception as e:
            logger.warning(f"Scroll error: {e}")
    
    def find_and_click_ad(self):
        """Find and click POPUP/SOCIALBAR ads like in your screenshot"""
        try:
            logger.info("Looking for POPUP and SOCIALBAR ads...")
            
            # POPUP AD SELECTORS (like your Facebook notification ad)
            popup_selectors = [
                # Notification style popups (top right, top left, bottom)
                "[class*='notification']",
                "[class*='popup']",
                "[class*='popup-container']",
                "[class*='popup-content']",
                "[class*='modal']",
                "[class*='modal-dialog']",
                "[class*='alert']",
                "[class*='toast']",
                "[class*='message']",
                
                # Social bar ads
                "[class*='social-bar']",
                "[class*='socialbar']",
                "[class*='social-float']",
                "[class*='floating-bar']",
                "[class*='float-ads']",
                "[class*='sticky-ads']",
                "[class*='bottom-bar']",
                "[class*='top-bar']",
                
                # Click here buttons
                "button:contains('Click Here')",
                "a:contains('Click Here')",
                "[class*='click-here']",
                "[class*='cta']",
                "[class*='cta-button']",
                
                # Banner ads with images
                "img[src*='ad']",
                "img[src*='ads']",
                "img[alt*='ad' i]",
                "img[alt*='click' i]",
                "img[alt*='sponsored' i]",
                
                # Common ad containers
                "[class*='ad-container']",
                "[class*='ads-container']",
                "[class*='banner']",
                "[class*='banner-ad']",
                
                # Divs with ad text
                "div:contains('Sponsored')",
                "div:contains('Advertisement')",
                "div:contains('AD')",
                
                # Iframes (ad networks use these)
                "iframe",
                
                # Specific positions (fixed position = likely popup)
                "[style*='position: fixed']",
                "[style*='position:fixed']",
                "[style*='z-index: 999']",
                "[style*='z-index:999']",
            ]
            
            # Also search by TEXT content for "Click Here"
            click_here_xpath = "//*[contains(text(), 'Click Here') or contains(text(), 'click here') or contains(text(), 'CLICK HERE')]"
            
            all_ads = []
            
            # Try CSS selectors
            for selector in popup_selectors:
                try:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    for el in elements:
                        try:
                            if el.is_displayed():
                                size = el.size
                                if size['height'] > 20 and size['width'] > 50:
                                    all_ads.append(('css', el))
                                    logger.info(f"Found popup element: {selector[:30]}...")
                        except:
                            continue
                except:
                    continue
            
            # Try XPath for text-based ads
            try:
                text_ads = self.driver.find_elements(By.XPATH, click_here_xpath)
                for el in text_ads:
                    try:
                        if el.is_displayed():
                            # Get parent clickable element
                            parent = el.find_element(By.XPATH, "..")
                            if parent.is_displayed():
                                all_ads.append(('xpath', parent))
                                logger.info("Found 'Click Here' text ad")
                    except:
                        all_ads.append(('xpath', el))
            except:
                pass
            
            # Also look for ANY clickable element with "Click" in text
            try:
                all_clickables = self.driver.find_elements(By.XPATH, "//a | //button")
                for el in all_clickables:
                    try:
                        text = el.text.lower()
                        if 'click' in text or 'visit' in text or 'learn more' in text:
                            if el.is_displayed() and el not in [a[1] for a in all_ads]:
                                all_ads.append(('clickable', el))
                                logger.info(f"Found clickable with text: {text[:20]}")
                    except:
                        continue
            except:
                pass
            
            if not all_ads:
                logger.info("No popup/socialbar ads found")
                return False
            
            logger.info(f"Found {len(all_ads)} potential ads")
            
            # Pick random ad (prefer first few)
            ad_type, ad = random.choice(all_ads[:min(5, len(all_ads))])
            
            # Scroll to ad if needed
            try:
                self.driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", ad)
                time.sleep(random.uniform(1, 3))
            except:
                pass  # Fixed position popups don't need scrolling
            
            # Hover first (human-like)
            try:
                ActionChains(self.driver).move_to_element(ad).pause(random.uniform(0.5, 1)).perform()
            except:
                pass
            
            # CLICK THE AD
            logger.info(f"CLICKING AD! (type: {ad_type})")
            
            try:
                ad.click()
            except:
                try:
                    self.driver.execute_script("arguments[0].click();", ad)
                except Exception as e:
                    logger.error(f"Click failed: {e}")
                    return False
            
            # Wait for popup/new tab
            time.sleep(4)
            
            # Handle new window/tab
            current_handles = self.driver.window_handles
            
            if len(current_handles) > 1:
                # New tab opened
                new_window = [h for h in current_handles if h != self.main_window][0]
                self.driver.switch_to.window(new_window)
                logger.info("Switched to ad popup/tab")
                
                # SCROLL FOR 30-40 SECONDS
                ad_scroll_time = random.randint(30, 40)
                logger.info(f"Scrolling ad for {ad_scroll_time} seconds...")
                self.human_like_scroll(ad_scroll_time)
                
                # Close and return
                self.driver.close()
                self.driver.switch_to.window(self.main_window)
                logger.info("Returned to main")
                return True
            else:
                # Same tab redirect or popup overlay
                logger.info("Ad opened in same window")
                
                # Scroll for 30-40 seconds
                ad_scroll_time = random.randint(30, 40)
                logger.info(f"Scrolling for {ad_scroll_time} seconds...")
                self.human_like_scroll(ad_scroll_time)
                
                # Try to close popup if there's a close button
                try:
                    close_buttons = self.driver.find_elements(By.CSS_SELECTOR, "[class*='close'], [class*='dismiss'], .x, .close-btn")
                    for btn in close_buttons:
                        if btn.is_displayed():
                            btn.click()
                            logger.info("Closed popup")
                            time.sleep(1)
                            break
                except:
                    pass
                
                # Go back if needed
                try:
                    current_url = self.driver.current_url
                    if target_url not in current_url:
                        self.driver.back()
                        time.sleep(2)
                        logger.info("Went back")
                except:
                    pass
                
                return True
                
        except Exception as e:
            logger.warning(f"Ad click error: {e}")
        
        return False
    
    def click_navigation_link(self, target_domain):
        """Click About, Contact, etc."""
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
                text = link.text.strip() or "Nav"
                logger.info(f"Clicking: {text}")
                
                self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", link)
                time.sleep(random.uniform(1, 3))
                link.click()
                
                time.sleep(random.uniform(4, 8))
                self.human_like_scroll(random.randint(15, 25))
                return True
                
        except Exception as e:
            logger.warning(f"Nav click failed: {e}")
        
        return False
    
    def click_random_internal_link(self, target_domain):
        """Click any internal link"""
        try:
            links = self.driver.find_elements(By.TAG_NAME, "a")
            internal_links = []
            
            for link in links:
                try:
                    href = link.get_attribute('href')
                    if href and target_domain in href and link.is_displayed():
                        if not href.startswith('#') and not href.startswith('javascript'):
                            internal_links.append(link)
                except:
                    continue
            
            if internal_links:
                link = random.choice(internal_links[:8])
                logger.info("Clicking article/link...")
                
                self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", link)
                time.sleep(random.uniform(2, 4))
                link.click()
                
                time.sleep(random.uniform(5, 10))
                self.human_like_scroll(random.randint(12, 20))
                return True
                
        except Exception as e:
            logger.warning(f"Link click failed: {e}")
        
        return False
    
    def run_session(self):
        """Run session with POPUP AD clicking"""
        from database import storage
        
        targets = self.get_target_urls()
        if not targets:
            logger.error("No targets!")
            return
        
        target_url = random.choice(targets)
        target_domain = target_url.split('/')[2] if '//' in target_url else target_url
        
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
            time.sleep(random.uniform(5, 8))
            self.human_like_scroll(random.randint(15, 25))
            session_data['pages_visited'] += 1
            
            # Wait for ads to load (popups often appear after delay)
            time.sleep(3)
            
            # TRY MULTIPLE TIMES TO CLICK ADS
            for attempt in range(3):  # Try 3 times
                logger.info(f"=== AD ATTEMPT {attempt + 1} ===")
                if self.find_and_click_ad():
                    session_data['ads_clicked'] += 1
                    session_data['pages_visited'] += 1
                    time.sleep(2)  # Wait before looking for more
                else:
                    break
            
            # Navigation pages
            for i in range(3):
                logger.info(f"=== NAVIGATION PAGE {i + 1} ===")
                
                # Try nav link
                if self.click_navigation_link(target_domain):
                    session_data['pages_visited'] += 1
                    
                    # Try ads on this page
                    time.sleep(3)
                    if self.find_and_click_ad():
                        session_data['ads_clicked'] += 1
                        session_data['pages_visited'] += 1
                else:
                    # Try random link
                    if self.click_random_internal_link(target_domain):
                        session_data['pages_visited'] += 1
            
            # Ensure 4-5 minutes
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
