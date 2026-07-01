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
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

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
        
        # IMPORTANT: Allow all popups and notifications
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
        """Find and click ads - IMPROVED VERSION"""
        try:
            logger.info("=== SEARCHING FOR ADS ===")
            
            # Wait for page to fully load including ads
            time.sleep(5)
            
            # METHOD 1: Find by TEXT content (most reliable for popups)
            text_patterns = [
                "Click Here", "click here", "CLICK HERE",
                "Learn More", "learn more", "LEARN MORE",
                "Visit", "VISIT", "visit",
                "Open", "OPEN", "open",
                "Continue", "CONTINUE", "continue",
                "Get Started", "GET STARTED",
                "Download", "DOWNLOAD", "download",
                "Install", "INSTALL", "install",
                "Play", "PLAY", "play",
                "Watch", "WATCH", "watch",
                "Subscribe", "SUBSCRIBE", "subscribe",
                "Join", "JOIN", "join",
                "Sign Up", "SIGN UP", "sign up",
                "Register", "REGISTER", "register",
                "Buy Now", "BUY NOW", "buy now",
                "Shop Now", "SHOP NOW", "shop now",
                "Save", "SAVE", "save",
                "Claim", "CLAIM", "claim",
                "Verify", "VERIFY", "verify",
                "Secure", "SECURE", "secure",
                "Protect", "PROTECT", "protect",
                "Warning", "WARNING", "warning",
                "Alert", "ALERT", "alert",
                "Important", "IMPORTANT", "important",
                "Don't worry", "DON'T WORRY", "don't worry",
                "Facebook", "FACEBOOK", "facebook",
                "Account", "ACCOUNT", "account",
                "Hacked", "HACKED", "hacked"
            ]
            
            # Search for elements containing these texts
            for pattern in text_patterns:
                try:
                    # Try to find by XPath
                    xpath = f"//*[contains(text(), '{pattern}')]"
                    elements = self.driver.find_elements(By.XPATH, xpath)
                    
                    for el in elements:
                        try:
                            if el.is_displayed():
                                # Get the clickable parent
                                parent = el.find_element(By.XPATH, "..")
                                
                                # Check if it's a button, link, or has onclick
                                tag = el.tag_name.lower()
                                
                                if tag in ['a', 'button'] or parent.tag_name in ['a', 'button']:
                                    logger.info(f"Found ad with text: '{pattern}'")
                                    
                                    # Scroll to it
                                    self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", el)
                                    time.sleep(2)
                                    
                                    # Hover
                                    ActionChains(self.driver).move_to_element(el).pause(0.5).perform()
                                    
                                    # CLICK IT
                                    logger.info(f"CLICKING AD with text: {pattern}")
                                    try:
                                        el.click()
                                    except:
                                        parent.click()
                                    
                                    return self.handle_ad_click()
                                    
                        except Exception as e:
                            continue
                except:
                    continue
            
            # METHOD 2: Find by CSS selectors (for image/button ads)
            ad_selectors = [
                # Images that are clickable
                "img[onclick]",
                "img[style*='cursor: pointer']",
                "img[role='button']",
                
                # Divs that look like buttons
                "div[onclick]",
                "div[role='button']",
                "div[style*='cursor: pointer']",
                
                # Notification/popup styles
                "[style*='position: fixed']",
                "[style*='position:fixed']",
                "[style*='z-index: 999']",
                "[style*='z-index: 1000']",
                "[style*='z-index: 9999']",
                
                # Common ad containers
                "[class*='popup']",
                "[class*='modal']",
                "[class*='notification']",
                "[class*='toast']",
                "[class*='alert']",
                "[class*='message']",
                "[class*='banner']",
                "[class*='sticky']",
                "[class*='floating']",
                "[class*='float']",
                "[class*='social']",
                "[class*='bar']",
                
                # Iframes (ads often load in iframes)
                "iframe",
                
                # Buttons
                "button:not([type='submit'])",
                "button[class*='close']",
                "button[class*='dismiss']",
                
                # Links with no text (image ads)
                "a[href]:empty",
                "a img",
            ]
            
            for selector in ad_selectors:
                try:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    logger.info(f"Selector '{selector[:30]}...' found {len(elements)} elements")
                    
                    for el in elements:
                        try:
                            if el.is_displayed():
                                size = el.size
                                if size['height'] > 30 and size['width'] > 50:
                                    logger.info(f"Found clickable element: {el.tag_name} {size}")
                                    
                                    # Scroll to it
                                    self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", el)
                                    time.sleep(2)
                                    
                                    # Hover
                                    ActionChains(self.driver).move_to_element(el).pause(0.5).perform()
                                    
                                    # CLICK
                                    logger.info(f"CLICKING element: {el.tag_name}")
                                    el.click()
                                    
                                    return self.handle_ad_click()
                                    
                        except Exception as e:
                            continue
                except Exception as e:
                    continue
            
            # METHOD 3: JavaScript injection - find all clickable elements
            logger.info("Trying JavaScript method...")
            try:
                clickable = self.driver.execute_script("""
                    var elements = document.querySelectorAll('a, button, div[onclick], span[onclick], img[onclick], [role="button"], [style*="cursor: pointer"]');
                    var visible = [];
                    for (var i = 0; i < elements.length; i++) {
                        var rect = elements[i].getBoundingClientRect();
                        if (rect.width > 50 && rect.height > 30 && rect.top > 0 && rect.top < window.innerHeight) {
                            visible.push({
                                element: elements[i],
                                text: elements[i].textContent || '',
                                tag: elements[i].tagName
                            });
                        }
                    }
                    return visible;
                """)
                
                logger.info(f"JavaScript found {len(clickable)} clickable elements")
                
                if clickable and len(clickable) > 0:
                    # Pick a random one from top half of page (where ads usually are)
                    top_elements = [e for e in clickable if e.get('text') and len(e.get('text', '').strip()) > 0][:10]
                    
                    if top_elements:
                        chosen = random.choice(top_elements)
                        logger.info(f"Clicking JS element: {chosen.get('tag')} with text: {chosen.get('text', 'no text')[:50]}")
                        
                        # Click via JavaScript
                        self.driver.execute_script("arguments[0].click();", chosen.get('element'))
                        return self.handle_ad_click()
                        
            except Exception as e:
                logger.error(f"JavaScript click failed: {e}")
            
            logger.info("No ads found after all methods")
            return False
            
        except Exception as e:
            logger.error(f"Ad find error: {e}")
        
        return False
    
    def handle_ad_click(self):
        """Handle the ad click - wait and scroll"""
        try:
            time.sleep(4)
            
            # Check if new tab opened
            current_handles = self.driver.window_handles
            
            if len(current_handles) > 1:
                # Switch to new tab
                new_window = [h for h in current_handles if h != self.main_window][0]
                self.driver.switch_to.window(new_window)
                logger.info("Switched to ad tab/window")
                
                # SCROLL FOR 30-40 SECONDS
                scroll_time = random.randint(30, 40)
                logger.info(f"Scrolling ad page for {scroll_time} seconds...")
                self.human_like_scroll(scroll_time)
                
                # Close and return
                self.driver.close()
                self.driver.switch_to.window(self.main_window)
                logger.info("Returned to main page")
                return True
            else:
                # Same tab
                logger.info("Ad opened in same tab")
                scroll_time = random.randint(30, 40)
                self.human_like_scroll(scroll_time)
                
                # Try to go back
                try:
                    self.driver.back()
                    time.sleep(2)
                except:
                    pass
                
                return True
                
        except Exception as e:
            logger.error(f"Handle ad click error: {e}")
            return False
    
    def click_navigation_link(self, target_domain):
        """Click About, Contact, etc."""
        try:
            nav_keywords = ['about', 'contact', 'services', 'products', 'blog', 'news', 'privacy', 'terms']
            
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
                logger.info(f"Clicking navigation: {text}")
                
                self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", link)
                time.sleep(2)
                link.click()
                
                time.sleep(random.uniform(4, 8))
                self.human_like_scroll(random.randint(15, 25))
                return True
                
        except Exception as e:
            logger.warning(f"Nav click failed: {e}")
        
        return False
    
    def run_session(self):
        """Run session with AGGRESSIVE ad clicking"""
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
            
            # Wait for ads to load (popups often appear after delay)
            logger.info("Waiting 10 seconds for ads to load...")
            time.sleep(10)
            
            # Scroll a bit first
            self.human_like_scroll(random.randint(10, 15))
            session_data['pages_visited'] += 1
            
            # TRY TO CLICK ADS MULTIPLE TIMES
            for attempt in range(5):  # Try 5 times on main page
                logger.info(f"=== AD ATTEMPT {attempt + 1} on main page ===")
                if self.find_and_click_ad():
                    session_data['ads_clicked'] += 1
                    session_data['pages_visited'] += 1
                    logger.info(f"Ad clicked! Total ads: {session_data['ads_clicked']}")
                    
                    # Wait and look for more ads
                    time.sleep(5)
                else:
                    logger.info("No ad found this attempt")
                    # Scroll more and try again
                    self.human_like_scroll(5)
            
            # Navigation pages
            for i in range(3):
                logger.info(f"=== NAVIGATION PAGE {i + 1} ===")
                
                if self.click_navigation_link(target_domain):
                    session_data['pages_visited'] += 1
                    
                    # Look for ads on this page too
                    time.sleep(5)
                    for attempt in range(3):
                        if self.find_and_click_ad():
                            session_data['ads_clicked'] += 1
                            session_data['pages_visited'] += 1
                            time.sleep(3)
                        else:
                            break
            
            # Ensure 4-5 minute duration
            elapsed = time.time() - session_data['start_time']
            target_duration = random.randint(240, 300)
            
            if elapsed < target_duration:
                wait_time = target_duration - elapsed
                logger.info(f"Waiting extra {wait_time:.0f}s...")
                time.sleep(wait_time)
            
            total_duration = time.time() - session_data['start_time']
            
            # Save results
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
            
            logger.info(f"✓ COMPLETE: {total_duration:.0f}s, {session_data['pages_visited']} pages, {session_data['ads_clicked']} ads clicked")
            
        except Exception as e:
            logger.error(f"✗ FAILED: {e}")
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
