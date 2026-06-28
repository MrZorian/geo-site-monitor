@app.route('/api/targets')
def get_targets():
    """Get all target URLs"""
    urls = ConfigSetting.get('TARGET_URLS', 'https://example.com')
    return jsonify({
        'targets': [url.strip() for url in urls.split(',') if url.strip()]
    })

@app.route('/api/stats')
def get_stats():
    stats = storage.get_stats()
    stats['target_stats'] = storage.get_stats_by_target()
    stats['proxy_count'] = len(ConfigSetting.get('PROXY_LIST', '').split(',')) if ConfigSetting.get('PROXY_LIST') else 0
    return jsonify(stats)
