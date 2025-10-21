import hashlib
import itertools
from flask import request
import threading
import time

# Global variables to store cracking state
found_password = None
is_running = False

def crack_hash_tool(flask_request):
    """
    Crack 6-digit numeric hashes using brute force
    """
    global found_password, is_running
    data = flask_request.get_json()
    hash_value = data.get('hash')
    algorithm = data.get('algorithm', 'md5').lower()
    
    if not hash_value:
        return {'error': 'Hash value required'}
    
    # Reset state
    found_password = None
    is_running = False
    
    # Start cracking in background thread
    thread = threading.Thread(target=crack_password, args=(hash_value, algorithm))
    thread.start()
    
    return {'status': 'started', 'message': 'Cracking process initiated'}

def crack_password(hash_value, algorithm='md5'):
    """
    Brute force crack 6-digit numeric passwords
    """
    global found_password, is_running
    is_running = True
    start_time = time.time()
    
    # Try all 6-digit combinations (000000 to 999999)
    for i in range(1000000):
        if not is_running:
            break
            
        password = f"{i:06d}"
        if algorithm == 'md5':
            guess_hash = hashlib.md5(password.encode()).hexdigest()
        elif algorithm == 'sha1':
            guess_hash = hashlib.sha1(password.encode()).hexdigest()
        elif algorithm == 'sha256':
            guess_hash = hashlib.sha256(password.encode()).hexdigest()
            
        if guess_hash == hash_value:
            elapsed = time.time() - start_time
            found_password = {
                'password': password,
                'attempts': i+1,
                'time': round(elapsed, 2)
            }
            is_running = False
            return
    
    elapsed = time.time() - start_time
    found_password = {
        'password': None,
        'attempts': 1000000,
        'time': round(elapsed, 2)
    }
    is_running = False

def get_crack_status():
    """
    Get the status of the current cracking operation
    """
    global found_password, is_running
    return {
        'completed': not is_running,
        'result': found_password
    }