import sqlite3

db = sqlite3.connect('lab_cultural.db')
db.row_factory = sqlite3.Row
cur = db.cursor()

cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name")
tables = [r['name'] for r in cur.fetchall()]
print(f'Tables ({len(tables)}):')
for t in tables:
    cur.execute(f'PRAGMA table_info({t})')
    cols = cur.fetchall()
    cur.execute(f'PRAGMA foreign_key_list({t})')
    fks = cur.fetchall()
    print(f'\n=== {t} ===')
    for c in cols:
        pk = ' PK' if c['pk'] else ''
        print(f'  {c["name"]} ({c["type"]}){pk}')
    if fks:
        for fk in fks:
            print(f'  FK: {fk["from"]} -> {fk["table"]}.{fk["to"]}')
db.close()
