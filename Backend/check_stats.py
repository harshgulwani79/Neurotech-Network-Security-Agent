import urllib.request, json, time
time.sleep(2)
try:
    m = json.loads(urllib.request.urlopen('http://localhost:5000/api/memory').read())
    print(f'✅ Tier 1 Auto-Fix: {m["tier1_auto_fix"]}')
    print(f'✅ Tier 2 Pending: {m["tier2_pending"]}')
    print(f'✅ Tier 3 Escalate: {m["tier3_escalated"]}')
except Exception as e:
    print(f'❌ Error: {e}')
