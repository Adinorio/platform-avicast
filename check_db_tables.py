import sqlite3

conn = sqlite3.connect('db.sqlite3')
cursor = conn.cursor()
cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = cursor.fetchall()
image_processing_tables = [table for table in tables if 'image_processing' in table[0] or 'processing' in table[0]]
print('Image processing related tables:', image_processing_tables)
conn.close()
