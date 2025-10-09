#!/usr/bin/env python3
import sqlite3
import os

db_path = os.path.join(os.getcwd(), 'db.sqlite3')
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

tables_to_check = [
    'image_processing_imageevaluationresult',
    'image_processing_modelevaluationrun',
    'image_processing_modelperformancemetrics',
    'image_processing_speciesperformancemetrics',
    'image_processing_confusionmatrixentry'
]

print("Checking if migration 0011 target tables exist:")
for table in tables_to_check:
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table,))
    result = cursor.fetchone()
    status = "EXISTS" if result else "NOT FOUND"
    print(f"  {table}: {status}")

conn.close()



