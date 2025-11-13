# fix_db.py
import sqlite3

conn = sqlite3.connect("rutas.db")
cursor = conn.cursor()

# Verificar si la columna ya existe
cursor.execute("PRAGMA table_info(rutas)")
columns = [col[1] for col in cursor.fetchall()]
if "geometria" not in columns:
    cursor.execute("ALTER TABLE rutas ADD COLUMN geometria TEXT")
    print("✅ Campo 'geometria' añadido a la tabla 'rutas'.")
else:
    print("ℹ️ El campo 'geometria' ya existe.")

conn.commit()
conn.close()