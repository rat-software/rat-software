import psycopg2
from psycopg2.extras import execute_values
import csv

'''
CREATE TABLE qs_study(
    id SERIAL PRIMARY KEY,
    name VARCHAR NOT NULL,
    created_at TIMESTAMP,
    status INTEGER DEFAULT 0
);

CREATE TABLE qs_keyword(
    id SERIAL PRIMARY KEY,
    qs_study_id INTEGER NOT NULL,
    qs_geotarget_criterion_id INTEGER NOT NULL,
    qs_language_code_criterion_id INTEGER NOT NULL,
    keyword TEXT NOT NULL,
    created_at TIMESTAMP,
    status INTEGER DEFAULT 0
);

CREATE TABLE qs_keyword_ideas(
    id SERIAL PRIMARY KEY,
    qs_study_id INTEGER NOT NULL,
    qs_keyword_id INTEGER NOT NULL,
    keyword_idea TEXT NOT NULL,
    avg_monthly_searches INTEGER NOT NULL,
    competition TEXT NOT NULL,
    created_at TIMESTAMP
);

CREATE TABLE qs_geotarget(
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    canonical_name TEXT NOT NULL,
    country_code TEXT NOT NULL,
    target_type TEXT NOT NULL,
    criterion_id INTEGER NOT NULL
);

CREATE TABLE qs_language_code(
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    code TEXT NOT NULL,
    criterion_id INTEGER NOT NULL
);
'''

conn = psycopg2.connect(database="your_db", user="your_db_user", password="your_db_password", host="your_host", port="5432")
cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

x = 0

with open("languagecodes.csv") as csv_file:
    csv_reader = csv.reader(csv_file, delimiter=',', quotechar='"')
    for row in csv_reader:
        
        if x > 0:
            name = row[0]
            code = row[1]
            criterion_id = row[2]

            cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
            cur.execute("SELECT id from qs_language_code where criterion_id=%s",(criterion_id,))
            conn.commit()
            criterion_id_check = cur.fetchone()

            if not criterion_id_check:
                print(row)
                cur.execute('INSERT INTO qs_language_code (name, code, criterion_id) VALUES (%s, %s, %s);', (name, code, criterion_id))
                conn.commit()
            
        x = x + 1

x = 0

with open("geotargets.csv", encoding="utf8") as csv_file:
    csv_reader = csv.reader(csv_file, delimiter=',', quotechar='"')
    for row in csv_reader:
        print(row)

        
        if x > 0:
            criterion_id = row[0]
            name = row[1]
            canonical_name = row[2]
            country_code = row[4]
            target_type = row[5]

            cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
            cur.execute("SELECT id from qs_geotarget where criterion_id=%s",(criterion_id,))
            conn.commit()
            criterion_id_check = cur.fetchone()

            if not criterion_id_check:
                print(row)
                cur.execute('INSERT INTO qs_geotarget (name, canonical_name, country_code, target_type, criterion_id) VALUES (%s, %s, %s, %s, %s);', (name, canonical_name, country_code, target_type, criterion_id))
                conn.commit()
            
        x = x + 1


conn.close()