#!/usr/bin/env python3
import os
import sys
import httpx

base = os.getenv('SOLARLEAD_BASE_URL', 'http://127.0.0.1:8000').rstrip('/')
with httpx.Client(timeout=15, follow_redirects=True) as c:
    for path in ['/health', '/ready']:
        r = c.get(base + path)
        print(path, r.status_code, r.text[:300])
        if r.status_code != 200:
            sys.exit(1)
print('Smoke-Test: OK')
