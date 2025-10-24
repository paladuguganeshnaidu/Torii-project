// assets/js/main.js – appended DoS detector UI handlers

function attachDoSDetectorHandlers() {
    const startBtn = document.getElementById('startBtn');
    const stopBtn = document.getElementById('stopBtn');
    const modeSelect = document.getElementById('modeSelect');
    const logPath = document.getElementById('logPath');

    if (!startBtn || !stopBtn || !modeSelect) return;

    modeSelect.addEventListener('change', () => {
        if (logPath) logPath.style.display = modeSelect.value === 'log' ? 'block' : 'none';
    });

    startBtn.addEventListener('click', () => {
        const mode = modeSelect.value;
        const path = mode === 'log' && logPath ? logPath.value : '';
        fetch('/api/start_dos', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ mode, log_path: path })
        }).then(r => r.json()).then(data => {
            alert(data.status);
        }).catch(e => alert('Failed to start detector'));
    });

    stopBtn.addEventListener('click', () => {
        fetch('/api/stop_dos', { method: 'POST' }).then(r => r.json()).then(data => {
            alert(data.status);
        }).catch(e => alert('Failed to stop detector'));
    });
}

function startDoSUpdates() {
    setInterval(() => {
        fetch('/api/incidents').then(r => r.json()).then(data => {
            try{
                document.getElementById('globalPPS').textContent = estimateGlobalPPS(data);
                document.getElementById('attackStatus').textContent = data.global_spike ? 'ATTACK' : 'Normal';
                document.getElementById('attackStatus').className = data.global_spike ? 'alert' : '';
                document.getElementById('blockedCount').textContent = (data.blocked_ips || []).length;

                const tbody = document.querySelector('#incidentsTable tbody');
                if (!tbody) return;
                tbody.innerHTML = '';

                const high = (data.high_traffic_ips || []).map(ip => [ip, 'Flood']);
                const anomalous = (data.anomalous_ips || []).filter(ip => !(data.high_traffic_ips || []).includes(ip)).map(ip => [ip, 'Anomaly']);
                [...high, ...anomalous].forEach(([ip, type]) => {
                    const tr = document.createElement('tr');
                    tr.innerHTML = `<td>${ip}</td><td>${type}</td><td><button onclick="unblockIP('${ip}')">Unblock</button></td>`;
                    tbody.appendChild(tr);
                });
            }catch(e){ console.warn('Render update failed', e); }
        }).catch(e => console.warn('Incident fetch failed', e));
    }, 2000);
}

function unblockIP(ip) {
    fetch('/api/unblock', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ ip })
    }).then(r => r.json()).then(data => alert(data.status)).catch(e => alert('Failed'));;
}

function estimateGlobalPPS(data) {
    // Simplified – real version uses packet rate from streaming stats
    try{
        const hi = (data.high_traffic_ips || []).length;
        return hi * 80 + (data.global_spike ? 12000 : 200);
    }catch(e){ return 0; }
}
