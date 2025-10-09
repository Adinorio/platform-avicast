#!/usr/bin/env python3
import sqlite3
import os

# Check if database exists
db_path = os.path.join(os.getcwd(), 'db.sqlite3')
if not os.path.exists(db_path):
    print("Database file not found!")
    exit(1)

# Connect to database
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Get all table names that start with image_processing_
cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE 'image_processing_%'")
tables = cursor.fetchall()

print("Image Processing tables in database:")
for table in tables:
    print(f"  - {table[0]}")

# Check if ProcessingResult table exists
processing_result_exists = any('processingresult' in table[0].lower() for table in tables)
print(f"\nProcessingResult table exists: {processing_result_exists}")

conn.close()



