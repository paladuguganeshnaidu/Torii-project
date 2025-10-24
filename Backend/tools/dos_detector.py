# Backend/tools/dos_detector.py
from .traffic_collector import PCAPCollector, LogCollector
from .analyzer import Analyzer
from .mitigator import Mitigator
import threading
import time

class DoSDetector:
    def __init__(self):
        self.analyzer = Analyzer()
        self.mitigator = Mitigator()
        self.collector = None
        self.running = False

    def start_packet_monitor(self, interface='eth0'):
        self.collector = PCAPCollector(interface, callback=self._pkt_callback)
        thread = threading.Thread(target=self.collector.start, daemon=True)
        thread.start()

    def start_log_monitor(self, log_path):
        self.collector = LogCollector(log_path, callback=self._log_callback)
        thread = threading.Thread(target=self.collector.start, daemon=True)
        thread.start()

    def _pkt_callback(self, pkt_data):
        try:
            self.analyzer.update_metrics(pkt_data.get('src'))
        except Exception:
            pass

    def _log_callback(self, batch):
        for entry in batch:
            try:
                self.analyzer.update_metrics(entry.get('src_ip'))
            except Exception:
                pass

    def detection_loop(self):
        self.running = True
        while self.running:
            alert = self.analyzer.get_anomalies()
            if any([alert.get('global_spike'), alert.get('per_ip_flood'), alert.get('z_score_alert')]):
                self.mitigator.handle_alert(alert)
            time.sleep(1)

    def start(self, mode='pcap', interface='eth0', log_path=None):
        self.running = True
        if mode == 'pcap':
            self.start_packet_monitor(interface)
        elif mode == 'log' and log_path:
            self.start_log_monitor(log_path)
        # Run detection loop in a background thread so start() is non-blocking
        loop_thread = threading.Thread(target=self.detection_loop, daemon=True)
        loop_thread.start()

    def stop(self):
        self.running = False
        try:
            if self.collector and hasattr(self.collector, 'stop'):
                self.collector.stop()
        except Exception:
            pass
