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
        chrome_options.add_argument('--window-size=1920,1080)
        chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        chrome_options.add_argument('--single-process')
        chrome_options.add_argument('--no-zygote')
        chrome_options.add_argument('--disable-setuid-sandbox')
        
        # Allow popups for ads
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
            
            # Store main window handle
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
            last_scroll = 0
            
            while time.time() - start < duration:
                # Random scroll amount
                scroll_pixels = random.randint(200, 800)
                scroll_direction = random.choice([1, -1])
                
                self.driver.execute_script(f"window.scrollBy(0, {scroll_pixels * scroll_direction});")
                last_scroll += scroll_pixels * scroll_direction
                
                # Random pause (reading time)
                pause = random.uniform(1, 4)
                time.sleep(pause)
                
                # Occasionally scroll back up slightly (re-reading)
                if random.random() < 0.25:
                    self.driver.execute_script(f"window.scrollBy(0, -{random.randint(100, 300)});")
                    time.sleep(random.uniform(2, 5))
                
                # Stop if reached bottom and been there a while
                scroll_height = self.driver.execute_script("return document.body.scrollHeight")
                current_pos = self.driver.execute_script("return window.pageYOffset + window.innerHeight")
                
                if current_pos >= scroll_height and (time.time() - start) > duration * 0.6:
                    break
                    
        except Exception as e:
            logger.warning(f"Scroll error: {e}")
    
    def find_and_click_ad(self):
        """Find and click on ads to earn money"""
        try:
            logger.info("Looking for ads to click...")
            
            # Multiple ad selectors
            ad_selectors = [
                "ins.adsbygoogle",
                "iframe[id*='google_ads']",
                "iframe[name*='google']",
                "div[id*='google_ad']",
                "[data-ad-slot]",
                "[data-ad-client]",
                ".ad",
                ".advertisement",
                ".banner-ad",
                "[class*='ad-']",
                "[class*='ads-']",
                "[id*='ad-']",
                "[id*='ads-']",
                "div[class*='advert']",
                "div[id*='advert']",
                "a[href*='ad.' i]",
                "a[href*='ads.' i]",
                "a[href*='click']",
                "a[href*='redirect']",
                "img[width='728'][height='90']",
                "img[width='300'][height='250']",
                "img[width='160'][height='600']",
                "a[target='_blank']",
                "[class*='sponsored']",
                "[class*='promoted']",
                "iframe:not([src*='youtube']):not([src*='vimeo'])"
            ]
            
            all_ads = []
            
            for selector in ad_selectors:
                try:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    for el in elements:
                        try:
                            if el.is_displayed() and el.size['height'] > 30 and el.size['width'] > 30:
                                if el.tag_name in ['a', 'button', 'iframe', 'ins', 'div', 'img']:
                                    all_ads.append(el)
                        except:
                            continue
                except:
                    continue
            
            # Remove duplicates
            unique_ads = []
            seen = set()
            for ad in all_ads:
                try:
                    ad_id = ad.id
                    if ad_id not in seen:
                        seen.add(ad_id)
                        unique_ads.append(ad)
                except:
                    unique_ads.append(ad)
            
            if not unique_ads:
                logger.info("No ads found on this page")
                return False
            
            logger.info(f"Found {len(unique_ads)} potential ads")
            
            # Pick random ad
            ad = random.choice(unique_ads[:5])
            
            # Scroll to ad
            self.driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", ad)
            time.sleep(random.uniform(2, 4))
            
            # Hover over ad first
            ActionChains(self.driver).move_to_element(ad).pause(random.uniform(0.5, 1.5)).perform()
            
            # Click the ad
            logger.info("CLICKING ON AD!")
            
            try:
                ad.click()
            except:
                self.driver.execute_script("arguments[0].click();", ad)
            
            # Wait for new tab/popup
            time.sleep(3)
            
            # Switch to new tab if opened
            current_handles = self.driver.window_handles
            if len(current_handles) > 1:
                new_window = [h for h in current_handles if h != self.main_window][0]
                self.driver.switch_to.window(new_window)
                logger.info("Switched to ad tab")
                
                # SCROLL AD PAGE FOR 30-40 SECONDS
                ad_scroll_time = random.randint(30, 40)
                logger.info(f"Scrolling ad page for {ad_scroll_time} seconds...")
                self.human_like_scroll(ad_scroll_time)
                
                # Close ad tab and return
                self.driver.close()
                self.driver.switch_to.window(self.main_window)
                logger.info("Returned to main page")
                return True
            else:
                # Ad opened in same tab
                logger.info("Ad opened in same tab")
                ad_scroll_time = random.randint(30, 40)
                logger.info(f"Scrolling ad page for {ad_scroll_time} seconds...")
                self.human_like_scroll(ad_scroll_time)
                
                # Go back
                self.driver.back()
                time.sleep(2)
                return True
                
        except Exception as e:
            logger.warning(f"Ad click failed: {e}")
        
        return False
    
    def click_navigation_link(self, target_domain):
        """Click navigation links like About, Contact, etc."""
        try:
            nav_keywords = ['about', 'contact', 'services', 'products', 'blog', 'news', 'portfolio', 'gallery']
            
            links = self.driver.find_elements(By.TAG_NAME, "a")
            nav_links = []
            
            for link in links:
                try:
                    text = link.text.lower().strip()
                    href = link.get_attribute('href') or ''
                    
                    is_nav = any(keyword in text or keyword in href.lower() for keyword in nav_keywords)
                    
                    if is_nav and link.is_displayed():
                        if target_domain in href or href.startswith('/'):
                            nav_links.append(link)
                except:
                    continue
            
            if nav_links:
                link = random.choice(nav_links)
                text = link.text.strip() or "Navigation"
                logger.info(f"Clicking navigation: {text}")
                
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
        """Click any random internal link"""
        try:
            links = self.driver.find_elements(By.TAG_NAME, "a")
            internal_links = []
            
            for link in links:
                try:
                    href = link.get_attribute('href')
                    if href and target_domain in href and link.is_displayed():
                        if not href.startswith('#') and not href.startswith('javascript') and not href.startswith('mailto'):
                            internal_links.append(link)
                except:
                    continue
            
            if internal_links:
                link = random.choice(internal_links[:8])
                logger.info("Clicking internal link...")
                
                self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", link)
                time.sleep(random.uniform(2, 4))
                link.click()
                
                time.sleep(random.uniform(5, 10))
                self.human_like_scroll(random.randint(12, 20))
                return True
                
        except Exception as e:
            logger.warning(f"Internal link failed: {e}")
        
        return False
    
    def run_session(self):
        """Run session with ad clicking and multi-page visits"""
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
            
            # STEP 1: Visit main page
            logger.info("=== STEP 1: Main Page ===")
            self.driver.get(target_url)
            time.sleep(random.uniform(4, 7))
            self.human_like_scroll(random.randint(15, 25))
            session_data['pages_visited'] += 1
            
            # STEP 2: Click ad on main page
            logger.info("=== STEP 2: Click Ad ===")
            if self.find_and_click_ad():
                session_data['ads_clicked'] += 1
                session_data['pages_visited'] += 1
            
            # STEP 3: Navigation page
            logger.info("=== STEP 3: Navigation ===")
            if self.click_navigation_link(target_domain):
                session_data['pages_visited'] += 1
                time.sleep(random.uniform(3, 6))
                if self.find_and_click_ad():
                    session_data['ads_clicked'] += 1
                    session_data['pages_visited'] += 1
            
            # STEP 4: Another page
            logger.info("=== STEP 4: Another Page ===")
            if self.click_random_internal_link(target_domain):
                session_data['pages_visited'] += 1
                time.sleep(random.uniform(3, 6))
                if self.find_and_click_ad():
                    session_data['ads_clicked'] += 1
                    session_data['pages_visited'] += 1
            
            # STEP 5: Final page
            logger.info("=== STEP 5: Final Page ===")
            if self.click_random_internal_link(target_domain):
                session_data['pages_visited'] += 1
                time.sleep(random.uniform(5, 10))
                self.human_like_scroll(random.randint(10, 15))
            
            # Ensure 4-5 minute duration
            elapsed = time.time() - session_data['start_time']
            target_duration = random.randint(240, 300)
            
            if elapsed < target_duration:
                wait_time = target_duration - elapsed
                logger.info(f"Waiting extra {wait_time:.0f}s...")
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
