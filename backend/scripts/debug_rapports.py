import sqlite3
from pathlib import Path

db = Path(__file__).resolve().parents[1] / 'db.sqlite3'
if not db.exists():
    print('DB not found at', db)
    raise SystemExit(1)

conn = sqlite3.connect(str(db))
cur = conn.cursor()
try:
    total = cur.execute('SELECT count(*) FROM core_rapport').fetchone()[0]
except Exception as e:
    print('Error reading core_rapport:', e)
    raise
print('total_rapports=', total)
print('--- détails (max 50) ---')
q = '''
SELECT r.id, r.titre, au.username as auteur, r.chantier_id,
       cu.username as chef_user, eu.username as chef_emp_user
FROM core_rapport r
LEFT JOIN auth_user au ON r.auteur_id=au.id
LEFT JOIN core_chantier ch ON r.chantier_id=ch.id
LEFT JOIN auth_user cu ON ch.chef_chantier=cu.id
LEFT JOIN core_employee ce ON ch.chef_chantier_employee=ce.id
LEFT JOIN auth_user eu ON ce.user_id=eu.id
LIMIT 50
'''
for row in cur.execute(q):
    print(row)

conn.close()
