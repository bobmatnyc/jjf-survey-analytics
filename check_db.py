#!/usr/bin/env python3
"""Quick script to check database table counts"""
import os
import psycopg2

def check_tables():
    db_url = os.environ.get('DATABASE_URL')
    if not db_url:
        print("ERROR: DATABASE_URL not found")
        return

    conn = psycopg2.connect(db_url)
    cur = conn.cursor()

    tables = ['surveys', 'survey_responses', 'survey_questions', 'survey_answers']

    print("\n=== Table Counts ===")
    for table in tables:
        cur.execute(f"SELECT COUNT(*) FROM {table};")
        count = cur.fetchone()[0]
        print(f"{table}: {count}")

    print("\n=== Sample Survey Data ===")
    cur.execute("SELECT survey_name, survey_type, response_count, is_empty FROM surveys LIMIT 10;")
    rows = cur.fetchall()
    if rows:
        for row in rows:
            print(f"Survey: {row[0]}, Type: {row[1]}, Responses: {row[2]}, Empty: {row[3]}")
    else:
        print("No surveys found in database")

    print("\n=== Check is_empty Column Type ===")
    cur.execute("SELECT survey_name, is_empty, pg_typeof(is_empty) FROM surveys LIMIT 5;")
    rows = cur.fetchall()
    for row in rows:
        print(f"Survey: {row[0]}, is_empty: {row[1]}, Type: {row[2]}")

    cur.close()
    conn.close()

if __name__ == '__main__':
    check_tables()
