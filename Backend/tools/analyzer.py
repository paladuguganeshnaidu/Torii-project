# Efficient DDoS / traffic analyzer
import time
from collections import deque, OrderedDict
from typing import Dict, List
from ..config import DOS_CONFIG


class TimeBucketCounter:
    """
    Count events into fixed-size time buckets (default 1s) within a sliding window.
    Keeps a deque of (bucket_ts, count) and a running total for O(1) updates.
    """
    def __init__(self, bucket_size: int = 1, window: int = 900):
        self.bucket_size = bucket_size
        self.window = window
        self.buckets: deque = deque()  # (bucket_ts, count)
        self.total = 0

    def _bucket_ts(self, ts: float) -> int:
        return int(ts) - (int(ts) % self.bucket_size)

    def add(self, ts: float = None, count: int = 1):
        if ts is None:
            ts = time.time()
        b = self._bucket_ts(ts)
        if self.buckets and self.buckets[-1][0] == b:
            bt, bc = self.buckets.pop()
            self.buckets.append((bt, bc + count))
        else:
            self.buckets.append((b, count))
        self.total += count
        self.purge_old(ts)

    def purge_old(self, now: float = None):
        if now is None:
            now = time.time()
        cutoff = int(now) - self.window
        while self.buckets and self.buckets[0][0] <= cutoff:
            _, c = self.buckets.popleft()
            self.total -= c

    def count_last(self, seconds: int) -> int:
        if seconds <= 0:
            return 0
        now = time.time()
        cutoff = int(now) - seconds
        s = 0
        for ts, c in reversed(self.buckets):
            if ts > cutoff:
                s += c
            else:
                break
        return s


class PerIPState:
    def __init__(self, minute_history=10):
        self.per_second = TimeBucketCounter(bucket_size=1, window=900)
        self.current_minute = int(time.time()) // 60
        self.current_minute_count = 0
        self.minute_history = deque(maxlen=minute_history)
        self.last_seen = time.time()

    def add_event(self, ts: float = None):
        if ts is None:
            ts = time.time()
        self.last_seen = ts
        self.per_second.add(ts, 1)
        minute = int(ts) // 60
        if minute == self.current_minute:
            self.current_minute_count += 1
        else:
            self.minute_history.append(self.current_minute_count)
            self.current_minute = minute
            self.current_minute_count = 1

    def purge(self, window: int):
        self.per_second.window = window
        self.per_second.purge_old()

    def recent_minute_counts(self) -> List[int]:
        return list(self.minute_history) + [self.current_minute_count]


class Analyzer:
    def __init__(self):
        cfg = DOS_CONFIG
        self.whitelist = set(cfg.get('whitelist', []))
        self.window = cfg.get('z_score_window', 900)
        thresholds = cfg.get('thresholds', {})
        self.threshold_pps_global = thresholds.get('pps_global', 10000)
        self.threshold_req_per_ip = thresholds.get('req_per_ip', 100)
        self.minute_history = cfg.get('minute_history', 10)
        self.max_ips = cfg.get('max_tracked_ips', 20000)
        self.eviction_seconds = cfg.get('eviction_seconds', 3600)

        self.global_counter = TimeBucketCounter(bucket_size=1, window=self.window)
        self.ip_states: "OrderedDict[str, PerIPState]" = OrderedDict()

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

    def _ensure_ip_state(self, ip: str) -> PerIPState:
        state = self.ip_states.get(ip)
        if state:
            self.ip_states.move_to_end(ip)
            return state
        if len(self.ip_states) >= self.max_ips:
            self.ip_states.popitem(last=False)
        state = PerIPState(minute_history=self.minute_history)
        self.ip_states[ip] = state
        return state

    def _evict_idle(self):
        now = time.time()
        keys_to_remove = []
        for ip, st in list(self.ip_states.items()):
            if now - st.last_seen > self.eviction_seconds:
                keys_to_remove.append(ip)
        for k in keys_to_remove:
            self.ip_states.pop(k, None)

    def update_metrics(self, src_ip: str, proto: int = None):
        now = time.time()
        self.global_counter.add(now, 1)
        if not src_ip:
            return
        state = self._ensure_ip_state(src_ip)
        state.add_event(now)
        state.purge(self.window)
        if len(self.ip_states) % 1000 == 0:
            self._evict_idle()

    def detect_global_spike(self) -> bool:
        return self.global_counter.count_last(1) > self.threshold_pps_global

    def detect_per_ip_flood(self) -> List[str]:
        offenders = []
        for ip, st in self.ip_states.items():
            if self.is_whitelisted(ip):
                continue
            pps = st.per_second.count_last(1)
            if pps > self.threshold_req_per_ip:
                offenders.append(ip)
        return offenders

    def calculate_z_score(self, ip: str) -> float:
        st = self.ip_states.get(ip)
        if not st:
            return 0.0
        counts = st.recent_minute_counts()
        if not counts or len(counts) <= 1:
            return 0.0
        current = counts[-1]
        history = counts[:-1]
        mean = sum(history) / len(history)
        var = sum((x - mean) ** 2 for x in history) / len(history)
        std = var ** 0.5
        if std < 1e-6:
            return 0.0
        return (current - mean) / std

    def get_anomalies(self) -> Dict:
        global_spike = self.detect_global_spike()
        ip_floods = self.detect_per_ip_flood()
        z_alerts = []
        for ip in list(self.ip_states.keys()):
            if self.is_whitelisted(ip):
                continue
            z = self.calculate_z_score(ip)
            if z > 3:
                z_alerts.append(ip)

        return {
            'global_spike': global_spike,
            'per_ip_flood': ip_floods,
            'z_score_alert': z_alerts,
            'tracked_ip_count': len(self.ip_states),
            'timestamp': time.time()
        }
