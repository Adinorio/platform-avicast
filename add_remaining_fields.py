#!/usr/bin/env python
import sqlite3

conn = sqlite3.connect('db.sqlite3')
cursor = conn.cursor()

# Add remaining missing fields one by one
remaining_fields = [
    'compressed_size bigint',
    'archive_path varchar(500)',
    'optimized_image varchar(100)',
    'thumbnail varchar(100)',
    'thumbnail_size bigint',
    'storage_tier varchar(20) DEFAULT "HOT"',
    'last_accessed datetime',
    'retention_days integer DEFAULT 365',
    'image_width integer',
    'image_height integer',
    'processing_status varchar(20) DEFAULT "PENDING"',
    'processing_duration bigint',
    'processing_step varchar(20)',
    'processing_error text',
    'processing_progress integer DEFAULT 0',
    'metadata text'
]

for field_def in remaining_fields:
    try:
        cursor.execute(f'ALTER TABLE image_processing_imageupload ADD COLUMN {field_def}')
        print(f'Added: {field_def.split()[0]}')
    except Exception as e:
        print(f'Error with {field_def}: {e}')

conn.commit()
conn.close()
print('Finished adding remaining fields')















