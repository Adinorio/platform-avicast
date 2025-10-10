#!/usr/bin/env python
import sqlite3

conn = sqlite3.connect('db.sqlite3')
cursor = conn.cursor()

# Rename the table
cursor.execute('ALTER TABLE image_processing_processingresult RENAME TO image_processing_imageprocessingresult')

# Verify the rename worked
cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE 'image_processing_%'")
tables = cursor.fetchall()
print('Tables after rename:')
for table in tables:
    print(f'  - {table[0]}')

conn.commit()
conn.close()
print('✅ Table renamed successfully')







