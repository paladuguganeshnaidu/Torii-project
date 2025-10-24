# Backend/tools/analyzer.py
from collections import defaultdict, deque
import time
from typing import Dict, List
from ..config import DOS_CONFIG

class Analyzer:
    def __init__(self):
        self.ip_requests = defaultdict(lambda: deque())  # {ip: deque[timestamps]}
        self.global_packets = deque()
        self.whitelist = set(DOS_CONFIG.get('whitelist', []))
        self.window = DOS_CONFIG.get('z_score_window', 900)  # seconds
        self.thresholds = DOS_CONFIG.get('thresholds', {'pps_global': 10000, 'req_per_ip': 100})

    def is_whitelisted(self, ip: str) -> bool:
        from ipaddress import ip_address, ip_network
        for net in self.whitelist:
            try:
                if ip_address(ip) in ip_network(net):
                    return True
            except Exception:
                if ip == net:
                    return True
        return False

    def update_metrics(self, src_ip: str, proto: int = None):
        now = time.time()
        self.global_packets.append(now)
        self.ip_requests[src_ip].append(now)

        # Clean old entries
        self._purge_old(self.global_packets)
        for q in list(self.ip_requests.values()):
            self._purge_old(q)

    def _purge_old(self, queue):
        cutoff = time.time() - self.window
        while queue and queue[0] < cutoff:
            queue.popleft()

    def detect_global_spike(self) -> bool:
        count = sum(1 for t in self.global_packets if t > time.time() - 1)
        return count > self.thresholds.get('pps_global', 10000)

    def detect_per_ip_flood(self) -> List[str]:
        now = time.time()
        threshold = self.thresholds.get('req_per_ip', 100)
        offenders = []
        for ip, timestamps in self.ip_requests.items():
            reqs = sum(1 for t in timestamps if t > now - 1)
            if reqs > threshold and not self.is_whitelisted(ip):
                offenders.append(ip)
        return offenders

    def calculate_z_score(self, ip: str) -> float:
        now = time.time()
        current = sum(1 for t in self.ip_requests[ip] if t > now - 60)
        history = []
        # Build last 10 minute buckets
        for x in range(1, 11):
            start = now - x*60 - 60
            end = now - x*60
            history.append(sum(1 for t in self.ip_requests[ip] if start < t <= end))
        if not history or max(history) == 0:
            return 0.0
        mean = sum(history) / len(history)
        std = (sum((x - mean) ** 2 for x in history) / len(history)) ** 0.5
        return (current - mean) / (std + 1e-5)

    def get_anomalies(self) -> Dict:
        global_spike = self.detect_global_spike()
        ip_floods = self.detect_per_ip_flood()
        z_alerts = [ip for ip in self.ip_requests if self.calculate_z_score(ip) > 3]

        return {
            'global_spike': global_spike,
            'per_ip_flood': list(set(ip_floods)),
            'z_score_alert': list(set(z_alerts)),
            'timestamp': time.time()
        }
