import sqlite3
from pathlib import Path
p=Path(__file__).resolve().parents[1]/'db.sqlite3'
conn=sqlite3.connect(str(p))
cur=conn.cursor()
print(cur.execute('SELECT id,username,email FROM auth_user WHERE id=4').fetchone())
conn.close()
