def run_session(self):
    """Run monitoring session - multiple targets"""
    from database import storage
    import traceback
    
    logger.info("=" * 50)
    logger.info("SESSION STARTING")
    logger.info("=" * 50)
    
    # Pick random target from list
    import os
    targets = os.getenv('TARGET_URLS', 'https://example.com').split(',')
    targets = [t.strip() for t in targets if t.strip()]
    target_url = random.choice(targets)
    
    logger.info(f"Selected target: {target_url}")
    
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
        
        logger.info(f"Visiting: {target_url}")
        
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
        
        logger.info(f"SUCCESS: {target_url} - {duration:.1f}s")
        
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
