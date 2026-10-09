"""Opt-in external decisions with a durable, fail-closed pilot budget."""
import json
import math
from contextlib import contextmanager
import os
import sqlite3
import threading
import time
from pathlib import Path
from urllib.parse import urlsplit
import httpx
from .decisions import Decision
from .storage import now

MODEL = 'gpt-5.6-luna'
ROUTE = 'openai/gpt-5.6-luna'
SYSTEM = ('Return JSON only with cooperate boolean, propagate boolean, target integer from '
          'neighbors or null, reason string <=160 characters. You control only your own legal '
          'cooperation, broadcast/withhold and optional single-neighbor target. Null broadcasts '
          'to all neighbors. Choose using local state; no extra fields or state edits.')


def settings():
    base = os.environ.get('BUTTERFLYLAB_LLM_BASE_URL', '').rstrip('/')
    parts = urlsplit(base)
    if base and (parts.scheme != 'https' or not parts.hostname or parts.username or parts.password or parts.query or parts.fragment):
        raise ValueError('Provider URL must be HTTPS without embedded credentials or query')
    price_in = os.environ.get('BUTTERFLYLAB_INPUT_CNY_PER_MILLION')
    price_out = os.environ.get('BUTTERFLYLAB_OUTPUT_CNY_PER_MILLION')
    source = os.environ.get('BUTTERFLYLAB_PRICE_SOURCE', '')
    verified = os.environ.get('BUTTERFLYLAB_PRICE_VERIFIED') == '1' and bool(source)
    try:
        rates = [float(price_in or 0), float(price_out or 0)]
    except ValueError:
        rates = [0, 0]
    if any(not math.isfinite(p) or not 0 < p <= 10000 for p in rates):
        verified = False
        rates = [0, 0]
    source = source.replace(os.environ.get('BUTTERFLYLAB_LLM_KEY') or '\0', '[redacted]')[:200]
    return {'model':MODEL, 'route':ROUTE, 'base_url':base,
            'enabled':os.environ.get('BUTTERFLYLAB_REAL_LLM_ENABLED') == '1' and bool(os.environ.get('BUTTERFLYLAB_LLM_KEY')),
            'price_verified':verified, 'price_source':source,
            'input_cny_per_million':rates[0], 'output_cny_per_million':rates[1],
            'max_calls':125, 'budget_cny':10, 'target_cny':5, 'max_output_tokens':256,
            'max_input_tokens':1500, 'concurrency':1, 'retries':0}


class Ledger:
    def __init__(self, path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.lock = threading.Lock()
        with self.connect() as con:
            con.execute('CREATE TABLE IF NOT EXISTS llm_calls (id INTEGER PRIMARY KEY, experiment TEXT, created_at TEXT, status TEXT, reserved_cny REAL, cost_cny REAL, input_tokens INTEGER, output_tokens INTEGER, reasoning_tokens INTEGER, seconds REAL, model TEXT, usage_estimated INTEGER, note TEXT)')

    @contextmanager
    def connect(self):
        con = sqlite3.connect(self.path, timeout=30)
        try:
            with con:
                yield con
        finally:
            con.close()

    def totals(self, experiment=None):
        with self.connect() as con:
            con.row_factory = sqlite3.Row
            where, args = (' WHERE experiment=?', (experiment,)) if experiment else ('', ())
            rows = [dict(r) for r in con.execute('SELECT * FROM llm_calls'+where,args)]
        return {'calls':len(rows), 'successes':sum(r['status']=='accepted' for r in rows),
                'failures':sum(r['status'] not in ['accepted','reserved'] for r in rows),
                'input_tokens':sum(r['input_tokens'] or 0 for r in rows),
                'output_tokens':sum(r['output_tokens'] or 0 for r in rows),
                'reasoning_tokens':sum(r['reasoning_tokens'] or 0 for r in rows),
                'cost_cny':sum(r['cost_cny'] if r['cost_cny'] is not None else r['reserved_cny'] for r in rows),
                'usage_estimated':any(r['usage_estimated'] for r in rows),
                'cost_basis':'Verified-rate estimate or conservative reservation; not a provider invoice',
                'input_target_exceeded':any((r['input_tokens'] or 0)>1500 and not r['usage_estimated'] for r in rows),
                'records':rows}

    def reserve(self, experiment, cost, probe=False):
        if not math.isfinite(cost) or cost <= 0:
            raise ValueError('Invalid budget reservation')
        with self.lock, self.connect() as con:
            con.execute('BEGIN IMMEDIATE')
            calls, spent = con.execute('SELECT count(*),coalesce(sum(coalesce(cost_cny,reserved_cny)),0) FROM llm_calls').fetchone()
            if calls >= 125 or spent+cost > 10:
                raise ValueError('Global pilot budget exhausted')
            if con.execute('SELECT count(*) FROM llm_calls WHERE input_tokens>1500 AND usage_estimated=0').fetchone()[0]:
                raise ValueError('Provider input target exceeded; operator review required')
            if probe and con.execute("SELECT count(*) FROM llm_calls WHERE experiment='connectivity'").fetchone()[0] >= 1:
                raise ValueError('Unverified-price connectivity allowance exhausted')
            cur = con.execute('INSERT INTO llm_calls(experiment,created_at,status,reserved_cny,usage_estimated) VALUES (?,?,?,?,?)',
                              (experiment, now(),'reserved',cost,1))
            return cur.lastrowid

    def finish(self, ident, row):
        with self.connect() as con:
            con.execute('UPDATE llm_calls SET status=?,cost_cny=?,input_tokens=?,output_tokens=?,reasoning_tokens=?,seconds=?,model=?,usage_estimated=?,note=? WHERE id=?',
                        (*[row[k] for k in ['status','cost_cny','input_tokens','output_tokens','reasoning_tokens','seconds','model','usage_estimated','note']], ident))


class RealProvider:
    def __init__(self, ledger, experiment, config=None, probe=False, cancel=None):
        self.ledger=ledger;self.experiment=experiment;self.config=config or settings()
        self.probe=probe;self.cancel=cancel;self.rows=[]
    def decide(self, context):
        cfg=self.config
        if self.cancel and self.cancel():raise InterruptedError('Cancelled before external request')
        if not cfg['enabled']:return None,'real API disabled; rule fallback'
        if not self.probe and not cfg['price_verified']:return None,'price unverified; rule fallback'
        user=json.dumps(context,separators=(',',':'),ensure_ascii=True)
        # ASCII bytes upper-bound normal BPE input, including a message-envelope allowance.
        allowance=len((SYSTEM+user).encode('ascii'))+64
        if allowance>1500:return None,'input budget exceeded; rule fallback'
        input_rate=cfg['input_cny_per_million'];output_rate=cfg['output_cny_per_million']
        reserve=(allowance*input_rate+256*output_rate)/1e6 if cfg['price_verified'] else 1.0
        try:ident=self.ledger.reserve(self.experiment,reserve,self.probe)
        except ValueError:return None,'global budget exhausted; rule fallback'
        row={'status':'failed','cost_cny':reserve,'input_tokens':allowance,'output_tokens':256,
             'reasoning_tokens':0,'model':None,'usage_estimated':1,'note':'Request failed; conservative reservation retained'}
        start=time.monotonic();action=None
        try:
            response=httpx.post(cfg['base_url']+'/chat/completions',
                headers={'Authorization':'Bearer '+os.environ['BUTTERFLYLAB_LLM_KEY']},timeout=30,
                json={'model':cfg['route'],'max_completion_tokens':256,'reasoning_effort':'low',
                      'response_format':{'type':'json_object'},'messages':[
                          {'role':'system','content':SYSTEM},{'role':'user','content':user}]})
            row['note']='HTTP '+str(response.status_code)
            response.raise_for_status()
            data=response.json();reported=data.get('model')
            if reported not in [MODEL,ROUTE]:raise ValueError('Unconfirmed model route')
            row['model']=reported
            usage=data.get('usage') or {}
            if isinstance(usage.get('prompt_tokens'),int) and isinstance(usage.get('completion_tokens'),int):
                row.update(input_tokens=usage['prompt_tokens'],output_tokens=usage['completion_tokens'],usage_estimated=0,
                           reasoning_tokens=(usage.get('completion_tokens_details') or {}).get('reasoning_tokens',0))
                if cfg['price_verified']:row['cost_cny']=(row['input_tokens']*input_rate+row['output_tokens']*output_rate)/1e6
            proposal=Decision(**json.loads(data['choices'][0]['message']['content']))
            if proposal.target is not None and proposal.target not in context['neighbors']:raise ValueError('Invalid neighbor')
            proposal.reason=proposal.reason.replace(os.environ['BUTTERFLYLAB_LLM_KEY'],'[redacted]')
            action=proposal.model_dump();row.update(status='accepted',note='Legal structured action; model route confirmed')
        except Exception:
            row['note']+='; rejected response or transport failure; rule fallback'
        finally:
            row['seconds']=time.monotonic()-start;self.ledger.finish(ident,row);self.rows.append(row)
        return action,'accepted' if action else 'provider failure or invalid action; rule fallback'
    def usage(self):
        return self.ledger.totals(self.experiment)
