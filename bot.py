def setup_driver(self):
    """Initialize Chrome driver for Railway"""
    import subprocess
    import os
    
    chrome_options = Options()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--window-size=1920,1080')
    chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
    
    # Proxy
    self.current_proxy = self.get_proxy()
    if self.current_proxy:
        chrome_options.add_argument(f'--proxy-server={self.current_proxy}')
        logger.info(f"Using proxy: {self.current_proxy}")
    
    # Get paths from system
    try:
        chrome_path = subprocess.run(['which', 'chromium'], capture_output=True, text=True).stdout.strip()
        driver_path = subprocess.run(['which', 'chromedriver'], capture_output=True, text=True).stdout.strip()
        
        logger.info(f"Chrome: {chrome_path}")
        logger.info(f"Chromedriver: {driver_path}")
        
        chrome_options.binary_location = chrome_path
        
        from selenium.webdriver.chrome.service import Service
        service = Service(driver_path)
        self.driver = webdriver.Chrome(service=service, options=chrome_options)
        
        logger.info("Driver initialized successfully")
        return True
        
    except Exception as e:
        logger.error(f"Driver init failed: {e}")
        return False
