from flask import Blueprint, request, jsonify
import threading
from functools import wraps
import time
from collections import deque

api_bp = Blueprint('api', __name__)

# Web Vulnerability Scanner removed. Provide a clear response for legacy clients.
@api_bp.route('/scan', methods=['POST'])
def start_scan_removed():
    return (jsonify({"error": "Web Vulnerability Scanner has been removed from this deployment."}), 410)
