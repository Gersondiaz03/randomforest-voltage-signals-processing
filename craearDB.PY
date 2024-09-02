import sqlite3
import hashlib
from datetime import datetime

def create_sqlite_connection():
    try:
        connection = sqlite3.connect('registros.db')
        return connection
    except sqlite3.Error as e:
        print(f"Error: {e}")
    return None

def create_tables():
    connection = create_sqlite_connection()
    if connection:
        cursor = connection.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS login (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                usuario TEXT NOT NULL,
                contrasena TEXT NOT NULL
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS adquisiciones (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                archivo_csv TEXT NOT NULL,
                fecha_guardado TEXT NOT NULL
            )
        ''')
        connection.commit()
        cursor.close()
        connection.close()

# Llama a esta función una vez para crear las tablas
create_tables()

def add_user(usuario, contrasena):
    connection = create_sqlite_connection()
    if connection:
        cursor = connection.cursor()
        hashed_password = hashlib.sha256(contrasena.encode()).hexdigest()
        cursor.execute("INSERT INTO login (usuario, contrasena) VALUES (?, ?)", (usuario, hashed_password))
        connection.commit()
        cursor.close()
        connection.close()

add_user('Alexis', '1234')