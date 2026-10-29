import sqlite3

def init_db():
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            email TEXT UNIQUE,
            password TEXT
        )
    ''')
    
    default_accounts = [
        ("customer@email.com", "customer1234"),
        ("vendor@email.com", "vendor1234"),
        ("staff@email.com", "staff1234"),
        ("partner@email.com", "partner1234"),
        ("dispatcher@email.com", "dispatcher1234")
    ]
    
    for email, password in default_accounts:
        try:
            cursor.execute("INSERT INTO users (email, password) VALUES (?, ?)", (email, password))
        except sqlite3.IntegrityError:
            pass
            
    conn.commit()
    conn.close()

def register_user(email, password):
    try:
        conn = sqlite3.connect("users.db")
        cursor = conn.cursor()
        cursor.execute("INSERT INTO users (email, password) VALUES (?, ?)", (email, password))
        conn.commit()
        conn.close()
        return True
    except sqlite3.IntegrityError:
        return False

def check_login(email, password):
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE email = ? AND password = ?", (email, password))
    user = cursor.fetchone()
    conn.close()
    return user is not None

def get_password_by_email(email):
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()
    cursor.execute("SELECT password FROM users WHERE email = ?", (email,))
    row = cursor.fetchone()
    conn.close()
    return row[0] if row else None