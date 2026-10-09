"""Single-worker bounded jobs with durable states and cooperative round cancellation."""
import sqlite3, threading, time
from contextlib import contextmanager
from concurrent.futures import ThreadPoolExecutor
from .storage import now

ACTIVE=('QUEUED','RUNNING','CANCEL_REQUESTED')
class Jobs:
    def __init__(self,path,capacity=4):
        self.path=path;self.capacity=capacity;self.lock=threading.Lock();self.signals={};self.executor=ThreadPoolExecutor(max_workers=1)
        with self.connect() as con:
            if con.execute('PRAGMA user_version').fetchone()[0]>1:raise RuntimeError('Unsupported job schema')
            con.execute('CREATE TABLE IF NOT EXISTS jobs(id TEXT PRIMARY KEY,state TEXT,completed INTEGER,total INTEGER,budget_seconds REAL,error TEXT,updated_at TEXT)')
            con.execute('PRAGMA user_version=1')
    def recover(self):
        with self.connect() as con:con.execute("UPDATE jobs SET state='FAILED',error='Server interrupted task',updated_at=? WHERE state IN ('QUEUED','RUNNING','CANCEL_REQUESTED')",(now(),))
    @contextmanager
    def connect(self):
        con=sqlite3.connect(self.path,timeout=30)
        try:
            with con:yield con
        finally:con.close()
    def get(self,eid):
        with self.connect() as con:
            con.row_factory=sqlite3.Row;r=con.execute('SELECT * FROM jobs WHERE id=?',(eid,)).fetchone()
        return dict(r) if r else None
    def state(self,eid,state,error=None):
        with self.connect() as con:con.execute('UPDATE jobs SET state=?,error=?,updated_at=? WHERE id=?',(state,error,now(),eid))
    def progress(self,eid,done,total):
        with self.connect() as con:con.execute('UPDATE jobs SET completed=?,total=?,updated_at=? WHERE id=?',(done,total,now(),eid))
    def submit(self,eid,total,budget,work):
        with self.lock:
            with self.connect() as con:
                count=con.execute("SELECT count(*) FROM jobs WHERE state IN ('QUEUED','RUNNING','CANCEL_REQUESTED')").fetchone()[0]
                if count>=self.capacity:raise ValueError('Queue full: maximum four active jobs and one running worker')
                con.execute('INSERT INTO jobs VALUES (?,?,?,?,?,?,?)',(eid,'QUEUED',0,total,budget,None,now()))
            event=threading.Event();self.signals[eid]=event
            def run():
                start=time.monotonic()
                def cancelled():
                    if time.monotonic()-start>budget: event.set()
                    return event.is_set()
                try:
                    if event.is_set():self.state(eid,'CANCELLED');work(cancelled,True);return
                    self.state(eid,'RUNNING');work(cancelled,False)
                    self.state(eid,'CANCELLED' if event.is_set() else 'COMPLETED')
                except InterruptedError:self.state(eid,'CANCELLED')
                except Exception as error:self.state(eid,'FAILED',str(error))
                finally:self.signals.pop(eid,None)
            self.executor.submit(run)
    def cancel(self,eid):
        with self.lock:
            job=self.get(eid)
            if not job:raise KeyError('Task not found')
            if job['state'] not in ACTIVE:return job
            self.state(eid,'CANCEL_REQUESTED');signal=self.signals.get(eid)
            if signal:signal.set()
            return self.get(eid)
    def shutdown(self):
        for signal in list(self.signals.values()):signal.set()
        self.executor.shutdown(wait=True)
