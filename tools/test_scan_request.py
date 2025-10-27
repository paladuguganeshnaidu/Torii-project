import requests
url = 'http://127.0.0.1:5000/api/scan'
try:
    r = requests.post(url, json={'url': 'https://toriiminds.com'}, timeout=10)
    print('Status:', r.status_code)
    print('Headers:', r.headers.get('content-type'))
    text = r.text
    print('Body (first 1000 chars):')
    print(text[:1000])
except Exception as e:
    print('Request failed:', e)
