const socket = io();

// Load stats
async function loadStats() {
    const response = await fetch('/api/stats');
    const stats = await response.json();
    
    document.getElementById('todaySessions').textContent = stats.today_sessions;
    document.getElementById('successRate').textContent = stats.success_rate + '%';
    document.getElementById('avgLoadTime').textContent = stats.avg_load_time + 's';
    document.getElementById('totalSessions').textContent = stats.total_sessions;
    document.getElementById('targetUrl').textContent = stats.target_url;
}

// Load recent activity
async function loadActivity() {
    const response = await fetch('/api/logs?per_page=5');
    const data = await response.json();
    
    const activityList = document.getElementById('activityList');
    
    if (data.logs.length === 0) {
        activityList.innerHTML = '<p class="loading">No sessions yet</p>';
        return;
    }
    
    activityList.innerHTML = data.logs.map(log => `
        <div class="activity-item">
            <span class="activity-time">${log.timestamp}</span>
            <span class="activity-status ${log.status}">${log.status}</span>
            <span>${log.pages_visited} pages visited</span>
            <span>${log.session_duration}s duration</span>
        </div>
    `).join('');
}

// Initialize charts
function initCharts() {
    // Session history chart
    const sessionCtx = document.getElementById('sessionChart').getContext('2d');
    new Chart(sessionCtx, {
        type: 'bar',
        data: {
            labels: ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'],
            datasets: [{
                label: 'Sessions',
                data: [30, 35, 32, 38, 35, 28, 31],
                backgroundColor: 'rgba(99, 102, 241, 0.5)',
                borderColor: '#6366f1',
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            plugins: {
                legend: { display: false }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    grid: { color: 'rgba(255,255,255,0.1)' },
                    ticks: { color: '#94a3b8' }
                },
                x: {
                    grid: { display: false },
                    ticks: { color: '#94a3b8' }
                }
            }
        }
    });
    
    // Load time chart
    const loadCtx = document.getElementById('loadTimeChart').getContext('2d');
    new Chart(loadCtx, {
        type: 'line',
        data: {
            labels: ['00:00', '04:00', '08:00', '12:00', '16:00', '20:00'],
            datasets: [{
                label: 'Avg Load Time (s)',
                data: [2.1, 1.8, 2.5, 3.2, 2.8, 2.3],
                borderColor: '#10b981',
                backgroundColor: 'rgba(16, 185, 129, 0.1)',
                fill: true,
                tension: 0.4
            }]
        },
        options: {
            responsive: true,
            plugins: {
                legend: { display: false }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    grid: { color: 'rgba(255,255,255,0.1)' },
                    ticks: { color: '#94a3b8' }
                },
                x: {
                    grid: { display: false },
                    ticks: { color: '#94a3b8' }
                }
            }
        }
    });
}

// Run now button
document.getElementById('runNowBtn')?.addEventListener('click', async () => {
    const btn = document.getElementById('runNowBtn');
    btn.disabled = true;
    btn.textContent = 'Running...';
    
    try {
        const response = await fetch('/api/run-now', { method: 'POST' });
        const result = await response.json();
        
        if (result.success) {
            showToast('Session started! Check logs for results.');
        } else {
            showToast('Error: ' + result.error);
        }
    } catch (e) {
        showToast('Failed to start session');
    }
    
    setTimeout(() => {
        btn.disabled = false;
        btn.textContent = 'Run Session Now';
    }, 3000);
});

// Socket events
socket.on('session_complete', (data) => {
    showToast('Scheduled session completed!');
    loadStats();
    loadActivity();
});

function showToast(message) {
    const toast = document.getElementById('toast');
    toast.textContent = message;
    toast.classList.add('show');
    setTimeout(() => toast.classList.remove('show'), 3000);
}

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    loadStats();
    loadActivity();
    initCharts();
    
    // Refresh every 30 seconds
    setInterval(() => {
        loadStats();
        loadActivity();
    }, 30000);
});