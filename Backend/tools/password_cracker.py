import hashlib

COMMONS = ['password', '123456', 'qwerty', 'letmein', 'admin']

def crack_hash_tool(request):
    data = request.get_json(silent=True) or {}
    h = (data.get('hash') or '').strip().lower()
    algo = 'md5'
    if ':' in h:
        algo, h = h.split(':', 1)
    for pwd in COMMONS:
        digest = getattr(hashlib, algo)(pwd.encode()).hexdigest()
        if digest == h:
            return {'tool': 'password-cracker', 'hash': h, 'algorithm': algo, 'password': pwd, 'found': True}
    return {'tool': 'password-cracker', 'hash': h, 'algorithm': algo, 'found': False}
