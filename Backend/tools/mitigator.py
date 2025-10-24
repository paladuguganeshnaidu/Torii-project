# Backend/tools/mitigator.py
import subprocess
import time
from typing import Dict, Any
from ..utils import log_alert

class Mitigator:
    def __init__(self):
        self.blocked_ips = {}  # {ip: {'count': int, 'blocked_until': float}}
        self.base_duration = 300  # 5 minutes

    def block_ip(self, ip: str):
        if ip in self.blocked_ips:
            record = self.blocked_ips[ip]
            count = record['count'] + 1
            duration = self.base_duration * (2 ** (count - 1))  # Exponential backoff
            self.blocked_ips[ip]['count'] = count
        else:
            count = 1
            duration = self.base_duration
            self.blocked_ips[ip] = {'count': count, 'blocked_until': 0}

        expiry = time.time() + duration
        self.blocked_ips[ip]['blocked_until'] = expiry

        try:
            # Best-effort; requires running as root or with sudo privileges
            subprocess.run(['sudo', 'iptables', '-A', 'INPUT', '-s', ip, '-j', 'DROP'], check=True)
            log_alert(f"Blocked {ip} for {duration}s (attempt {count})")
        except subprocess.CalledProcessError as e:
            log_alert(f"Failed to block {ip}: {e}")
        except Exception as e:
            log_alert(f"Block error for {ip}: {e}")

    def release_expired_blocks(self):
        now = time.time()
        released = []
        for ip, data in list(self.blocked_ips.items()):
            if now > data['blocked_until']:
                try:
                    subprocess.run(['sudo', 'iptables', '-D', 'INPUT', '-s', ip, '-j', 'DROP'], check=True)
                    log_alert(f"Unblocked {ip}")
                except Exception:
                    log_alert(f"Failed to unblock {ip}")
                released.append(ip)
        for ip in released:
            del self.blocked_ips[ip]

    def handle_alert(self, alert: Dict):
        self.release_expired_blocks()
        offenders = set(alert.get('per_ip_flood', []) + alert.get('z_score_alert', []))
        for ip in offenders:
            if ip not in self.blocked_ips or time.time() > self.blocked_ips[ip]['blocked_until']:
                self.block_ip(ip)
