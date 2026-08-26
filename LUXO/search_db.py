import mysql.connector
import os
from dotenv import load_dotenv

load_dotenv()

db = mysql.connector.connect(
    host=os.getenv("DB_HOST"),
    user=os.getenv("DB_USER"),
    password=os.getenv("DB_PASSWORD"),
    database=os.getenv("DB_NAME"),
    port=int(os.getenv("DB_PORT"))
)
cursor = db.cursor()
cursor.execute("SHOW TABLES")
tables = [row[0] for row in cursor.fetchall()]

for table in tables:
    cursor.execute(f"DESCRIBE {table}")
    columns = [row[0] for row in cursor.fetchall() if "char" in row[1] or "text" in row[1]]
    for col in columns:
        try:
            cursor.execute(f"SELECT * FROM {table} WHERE {col} LIKE '%Nuestra meta%' LIMIT 1")
            if cursor.fetchone():
                print(f"FOUND in table {table}, column {col}")
        except:
            pass
db.close()
