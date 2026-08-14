import mysql.connector
import os
from dotenv import load_dotenv

load_dotenv()

try:
    db = mysql.connector.connect(
        host=os.getenv("DB_HOST"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        database=os.getenv("DB_NAME"),
        port=int(os.getenv("DB_PORT"))
    )
    cursor = db.cursor(dictionary=True)
    cursor.execute("SELECT ID_Manual, Nombre_Manual, Archivo_Blob FROM manuales WHERE Nombre_Manual LIKE %s", ("%ENFOQUE DIARIO%",))
    res = cursor.fetchall()
    for row in res:
        name = row["Nombre_Manual"]
        print(f"Found: {name}")
        with open(name.replace("/", "_") + ".xlsx", "wb") as f:
            f.write(row["Archivo_Blob"])
    db.close()
except Exception as e:
    print(e)
