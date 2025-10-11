#!/usr/bin/env python
import sqlite3

conn = sqlite3.connect('db.sqlite3')
cursor = conn.cursor()
cursor.execute('SELECT name FROM sqlite_master WHERE type="table" AND name LIKE "locations_%"')
tables = cursor.fetchall()
print('Locations tables:')
for table in tables:
    print(f'  - {table[0]}')
conn.close()