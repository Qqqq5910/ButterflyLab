"""Operator-only credential probe; never prints credentials or remote error bodies."""
import argparse
import json
import re
import os
from pathlib import Path
import httpx


def account_config(path):
    with Path(path).open(encoding='utf-8-sig') as stream:
        for line in stream:
            if 'tokenhub' in line.lower() and 'http' not in line.lower():
                section = [next(stream, '').strip() for _ in range(2)]
                url = next((x for x in section if x.startswith('https://')), None)
                key = next((x for x in section if x and x != url), None)
                if url and key:
                    return url.rstrip('/'), key
    raise ValueError('TokenHub section unavailable')


def public_routes():
    page = httpx.get('https://tokenhub.store', follow_redirects=True).text
    print('Public links:', sorted(set(re.findall(r'href="([^"]+)"', page)))[:60])
    for src in re.findall(r'src="([^"]+\.js)"', page):
        if 'page-' in src:
            text = httpx.get('https://tokenhub.store'+src).text
            print('Public route hints:', re.findall(r'.{0,60}(?:pricing|/api/).{0,90}', text)[:20])
    for route in ['/pricing', '/docs']:
        page = httpx.get('https://tokenhub.store'+route, follow_redirects=True).text
        print(route, 'model hints:', re.findall(r'.{0,120}(?:gpt-5\.6|luna).{0,200}', page)[:10])
        for src in re.findall(r'src="([^"]+\.js)"', page):
            if 'page-' in src:
                script = httpx.get('https://tokenhub.store'+src).text
                print(route, 'API hints:', re.findall(r'.{0,70}(?:/api/|\.get\(|pricing).{0,100}', script)[:20])


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--account')
    parser.add_argument('--connect', action='store_true')
    args = parser.parse_args()
    if not args.connect:
        public_routes()
    if args.account:
        base, key = account_config(args.account)
        if args.connect:
            from .llm import Ledger, RealProvider, settings
            os.environ.update(BUTTERFLYLAB_LLM_BASE_URL=base,BUTTERFLYLAB_LLM_KEY=key,BUTTERFLYLAB_REAL_LLM_ENABLED='1')
            ledger=Ledger(Path('data')/'llm-budget.sqlite3')
            provider=RealProvider(ledger,'connectivity',probe=True)
            action,status=provider.decide({'agent':0,'round':1,'role':'builder','resource':60,
                                         'mean_trust':.6,'informed':True,'neighbors':[1,2],
                                         'score':.55,'threshold':.5,'recent_events':[]})
            report={'requested_model':'gpt-5.6-luna','documented_route':'openai/gpt-5.6-luna',
                    'status':status,'action':action,'usage':provider.usage(),
                    'price_verified':False,'reason':'Account billing authentication unavailable; public quote is not an account-specific confirmed price',
                    'public_quote_usd_per_million':{'input':1,'output':6},
                    'bulk_paid_experiment':'blocked'}
            path=Path('output/research/phase2d-connectivity.json');path.parent.mkdir(parents=True,exist_ok=True)
            path.write_text(json.dumps(report,indent=2),encoding='utf-8')
            print(json.dumps(report,indent=2))
            raise SystemExit(0)
        response = httpx.get(base+'/models', headers={'Authorization':'Bearer '+key}, timeout=20)
        print('Model-list status:', response.status_code)
        if response.status_code == 200:
            data = response.json()
            models = data.get('data', [])
            chosen = [m for m in models if m.get('id') == 'gpt-5.6-luna']
            print('Requested model advertised:', bool(chosen))
            print('Model metadata fields:', sorted(chosen[0]) if chosen else [])
            print('Related advertised model IDs:', [m.get('id') for m in models if 'luna' in m.get('id','').lower() or '5.6' in m.get('id','')])
            routed = next((m for m in models if m.get('id') == 'openai/gpt-5.6-luna'), {})
            print('Exact namespaced route metadata:', {k:v for k,v in routed.items() if k in ['id','pricing','owned_by','name']})
        page = httpx.get('https://tokenhub.store/pricing').text
        start = page.find('GPT-5.6 Luna')
        print('Public Luna price row:', re.sub('<[^>]+>', ' ', page[start:start+4500]))
        for endpoint in ['/api/balance','/api/v1/billing/spending']:
            try:
                r = httpx.get('https://tokenhub.store'+endpoint, headers={'Authorization':'Bearer '+key},timeout=10)
                print('Read-only billing endpoint', endpoint, 'status', r.status_code)
            except httpx.HTTPError:
                print('Read-only billing endpoint', endpoint, 'unavailable')
