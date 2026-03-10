import urllib.request
import json

endpoints = [
    '/api/devices',
    '/api/anomalies', 
    '/api/audit-log'
]

for endpoint in endpoints:
    try:
        res = urllib.request.urlopen(f'http://localhost:5000{endpoint}', timeout=5)
        data = json.loads(res.read())
        print(f"✅ {endpoint}: Working")
        if endpoint == '/api/devices':
            print(f"   └─ {len(data)} devices found")
        elif endpoint == '/api/anomalies':
            t1 = len(data.get('tier1', []))
            t2 = len(data.get('tier2', []))
            t3 = len(data.get('tier3', []))
            print(f"   └─ Tier1: {t1}, Tier2: {t2}, Tier3: {t3}")
        elif endpoint == '/api/audit-log':
            print(f"   └─ {len(data.get('entries', []))} entries")
    except Exception as e:
        print(f"❌ {endpoint}: {e}")
