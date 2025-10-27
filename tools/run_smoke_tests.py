import io
import time
import json
import sys, os
# Ensure project root on path so Backend package can be imported when running this script
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from Backend.app import create_app
from Backend.tools import password_cracker as pc_mod

app = create_app()

# Use Flask test client
with app.test_client() as client:
    print('1) /api/url-scanner')
    r = client.post('/api/url-scanner', json={'url':'https://example.com'})
    print('status', r.status_code)
    try:
        print(r.get_json())
    except Exception:
        print(r.data[:400])
    print('\n---\n')

    print('2) /api/sms-spam-tester')
    r = client.post('/api/sms-spam-tester', json={'phone':'+1234567890','message':'You won CASH!!! Click now to claim your prize 111111'})
    print('status', r.status_code)
    print(r.get_json())
    print('\n---\n')

    print('3) /api/password-cracker (start)')
    # create MD5 of '000123' for quick find (but cracker searches 000000-999999)
    import hashlib
    sample = '000123'
    h = hashlib.md5(sample.encode()).hexdigest()
    r = client.post('/api/password-cracker', json={'hash': h, 'algorithm':'md5'})
    print('status', r.status_code)
    print(r.get_json())
    # wait a short while then check internal module status
    time.sleep(1.5)
    try:
        status = pc_mod.get_crack_status()
        print('crack status', status)
    except Exception as e:
        print('could not fetch crack status', e)
    print('\n---\n')

    print('4) /api/url-scanner with bad url')
    r = client.post('/api/url-scanner', json={'url':'not-a-url'})
    print('status', r.status_code)
    print(r.get_json())
    print('\n---\n')

    print('5) /api/web-recon')
    r = client.post('/api/web-recon', json={'url':'https://example.com'})
    print('status', r.status_code)
    print('json keys:', list((r.get_json() or {}).keys()))
    print('\n---\n')

    print('6) /api/scan (web vuln scanner)')
    r = client.post('/api/scan', json={'url':'https://example.com'})
    print('status', r.status_code)
    data = r.get_json()
    print(data)
    if r.status_code == 200 and 'scan_id' in data:
        scan_id = data['scan_id']
        print('polling scan result...')
        for _ in range(10):
            time.sleep(1)
            s = client.get(f'/api/scan/{scan_id}')
            js = None
            try:
                js = s.get_json()
            except:
                print('non-json response length', len(s.data))
            print('poll', s.status_code, js)
            if js and js.get('status') in ('complete','error'):
                break
    print('\n---\n')

    print('7) /api/email-analyzer (no file -> expect error)')
    r = client.post('/api/email-analyzer', data={})
    print('status', r.status_code)
    print(r.get_json())
    print('\n---\n')

    print('8) /api/malware-analyzer (upload tiny file)')
    sample_bytes = b'This is a harmless sample file for testing.'
    data = {'sample': (io.BytesIO(sample_bytes), 'sample.txt')}
    r = client.post('/api/malware-analyzer', data=data, content_type='multipart/form-data')
    print('status', r.status_code)
    try:
        print(r.get_json())
    except:
        print('non-json response', r.data[:400])
    print('\n---\n')

    print('9) /api/stegoshield-inspector (encode text)')
    # create a small red PNG via bytes using PIL if available; otherwise skip
    try:
        from PIL import Image
        import base64
        img = Image.new('RGB',(100,100),(255,0,0))
        buf = io.BytesIO(); img.save(buf,format='PNG'); buf.seek(0)
        data = { 'image': (buf,'test.png'), 'inspect_type':'txt', 'stego_mode':'encode', 'custom_text':'hello world' }
        r = client.post('/api/stegoshield-inspector', data=data, content_type='multipart/form-data')
        print('status', r.status_code)
        j = None
        try:
            j = r.get_json()
        except:
            print('non-json', r.data[:400])
        print(j)
    except Exception as e:
        print('PIL not available, skipping stegoshield test', e)
    print('\n---\n')

    print('10) DoS control endpoints (start/stop)')
    r = client.post('/api/start_dos', json={'mode':'pcap'})
    print('/api/start_dos', r.status_code, r.get_json())
    r = client.post('/api/stop_dos')
    print('/api/stop_dos', r.status_code, r.get_json())
    print('\n---\n')

    print('Smoke tests completed')