import sqlite3

def create_sqlite_connection():
    try:
        connection = sqlite3.connect('registros.db')
        return connection
    except sqlite3.Error as e:
        print(f"Error: {e}")
    return None

def print_table_contents():
    connection = create_sqlite_connection()
    if connection:
        cursor = connection.cursor()
        cursor.execute("SELECT * FROM adquisiciones")
        rows = cursor.fetchall()
        
        for row in rows:
            print(row)
        
        cursor.close()
        connection.close()

print(print_table_contents())