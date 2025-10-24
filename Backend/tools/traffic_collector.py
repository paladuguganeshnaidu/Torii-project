# Backend/tools/traffic_collector.py
import subprocess
import threading
import time
from typing import Callable, Dict, Any
import os

# Optional dependencies: watchdog (file monitoring) and scapy (packet sniffing).
# Render and other PaaS may not have these installed or allow packet capture.
try:
    from watchdog.observers import Observer
    from watchdog.events import FileSystemEventHandler
    WATCHDOG_AVAILABLE = True
except Exception:
    Observer = None
    FileSystemEventHandler = object
    WATCHDOG_AVAILABLE = False

try:
    from scapy.all import sniff
    SCAPY_AVAILABLE = True
except Exception:
    sniff = None
    SCAPY_AVAILABLE = False

from ..utils import log_alert

class PCAPCollector:
    def __init__(self, interface: str, callback: Callable):
        self.interface = interface
        self.callback = callback
        self.running = False

    def packet_handler(self, pkt):
        # Scapy packet classes use .haslayer and fields; check IP layer
        try:
            if pkt.haslayer('IP'):
                ip_layer = pkt.getlayer('IP')
                self.callback({
                    'src': ip_layer.src,
                    'dst': ip_layer.dst,
                    'proto': getattr(ip_layer, 'proto', None),
                    'time': time.time(),
                    'length': len(pkt)
                })
        except Exception:
            # Keep collector robust
            return

    def start(self):
        if not SCAPY_AVAILABLE:
            log_alert("PCAPCollector: scapy not available in this environment; packet capture disabled", 'dos')
            return
        self.running = True
        # sniff will block; use stop_filter to exit when running is False
        sniff(iface=self.interface, prn=self.packet_handler, store=False,
              stop_filter=lambda x: not self.running)

if WATCHDOG_AVAILABLE:
    class LogCollector(FileSystemEventHandler):
        def __init__(self, log_path: str, callback: Callable):
            self.log_path = log_path
            self.callback = callback
            self.observer = Observer()
            self.running = False

        def on_modified(self, event):
            # Only react to changes to the target file
            try:
                if os.path.abspath(event.src_path) == os.path.abspath(self.log_path):
                    self.read_lines()
            except Exception:
                pass

        def read_lines(self):
            try:
                with open(self.log_path, 'r', encoding='utf-8', errors='ignore') as f:
                    lines = f.readlines()
                batch = []
                for line in lines[-50:]:  # last 50 lines
                    ip = self.extract_ip(line)
                    if ip:
                        batch.append({'src_ip': ip, 'timestamp': time.time()})
                if batch:
                    self.callback(batch)
            except Exception:
                pass

        def extract_ip(self, line: str) -> str:
            import re
            match = re.search(r'\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b', line)
            return match.group(0) if match else None

        def start(self):
            self.running = True
            watch_dir = os.path.dirname(self.log_path) or '.'
            self.observer.schedule(self, path=watch_dir, recursive=False)
            self.observer.start()
            try:
                while self.running:
                    time.sleep(1)
            finally:
                self.observer.stop()
                self.observer.join()

        def stop(self):
            self.running = False
            try:
                self.observer.stop()
                self.observer.join()
            except Exception:
                pass
else:
    class LogCollector:
        def __init__(self, log_path: str, callback: Callable):
            self.log_path = log_path
            self.callback = callback
            self.running = False

        def read_lines(self):
            # watchdog not available — no-op
            log_alert("LogCollector: watchdog not available; log monitoring disabled", 'dos')

        def start(self):
            log_alert("LogCollector.start called but watchdog is not installed", 'dos')

        def stop(self):
            self.running = False
