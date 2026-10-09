"""Separate versioned SQLite world catalog, leaving the experiment schema intact."""
import json
import uuid
from .storage import Store,now

class WorldStore(Store):
    def migrate(self):
        with self.connect() as con:
            version=con.execute('PRAGMA user_version').fetchone()[0]
            if version>1: raise RuntimeError('World catalog schema newer than supported')
            con.executescript('''CREATE TABLE IF NOT EXISTS worlds (
              world_id TEXT PRIMARY KEY,name TEXT NOT NULL,parent_id TEXT,
              created_at TEXT NOT NULL,configuration TEXT NOT NULL);
              PRAGMA user_version=1;''')
    def save(self,name,config,parent=None):
        if parent: self.get(parent)
        eid=str(uuid.uuid4())
        with self.connect() as con:
            con.execute('INSERT INTO worlds VALUES (?,?,?,?,?)',(eid,name,parent,now(),json.dumps(config)))
        return self.get(eid)
    def get(self,eid):
        with self.connect() as con:
            row=con.execute('SELECT * FROM worlds WHERE world_id=?',(eid,)).fetchone()
            if row is None: raise KeyError('World not found')
            result=dict(row);result['configuration']=json.loads(result['configuration']);return result
    def list(self):
        with self.connect() as con:
            return [self.get(r[0]) for r in con.execute('SELECT world_id FROM worlds ORDER BY created_at DESC')]
