#!/usr/bin/env python3
import sqlite3
import os

# Connect to database
db_path = os.path.join(os.getcwd(), 'db.sqlite3')
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

print("Renaming table image_processing_imageprocessingresult to image_processing_processingresult...")

try:
    # Rename the table
    cursor.execute("ALTER TABLE image_processing_imageprocessingresult RENAME TO image_processing_processingresult")
    conn.commit()
    print("Table renamed successfully!")

    # Verify the rename worked
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE 'image_processing_%'")
    tables = cursor.fetchall()
    print("Updated image_processing tables:")
    for table in tables:
        print(f"  - {table[0]}")

except Exception as e:
    print(f"Error renaming table: {e}")
    conn.rollback()

conn.close()
