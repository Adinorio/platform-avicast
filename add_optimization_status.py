#!/usr/bin/env python
import sqlite3

conn = sqlite3.connect('db.sqlite3')
cursor = conn.cursor()

# Add the missing optimization_status field
try:
    cursor.execute('ALTER TABLE image_processing_imageupload ADD COLUMN optimization_status varchar(20) DEFAULT "pending"')
    print('Added optimization_status column')
except Exception as e:
    print(f'Error adding optimization_status: {e}')

conn.commit()
conn.close()















