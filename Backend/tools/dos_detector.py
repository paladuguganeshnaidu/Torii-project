"""
DoS Detector - REMOVED

This module previously provided packet/log based detection and mitigation
helpers. It has been replaced with a stub that raises at runtime. This
ensures any accidental usage fails fast and with a clear message.
"""

class DoSDetector:
    def __init__(self, *args, **kwargs):
        raise RuntimeError("DoSDetector has been removed from this deployment.")

    def start(self, *args, **kwargs):
        raise RuntimeError("DoSDetector has been removed from this deployment.")

    def stop(self, *args, **kwargs):
        raise RuntimeError("DoSDetector has been removed from this deployment.")
