import sqlite3
import bcrypt

def seed_user():
    # Use bcrypt directly to avoid passlib compatibility issues with bcrypt 4.x
    pw_bytes = b"password123"
    salt = bcrypt.gensalt()
    pw_hash = bcrypt.hashpw(pw_bytes, salt).decode('utf-8')
    
    conn = sqlite3.connect("rakshanet.db")
    c = conn.cursor()
    # Check if user exists
    c.execute("SELECT id FROM users WHERE email = 'admin@rakshanet.local'")
    if c.fetchone() is None:
        c.execute("""
            INSERT INTO users (name, email, role, password_hash, department)
            VALUES (?, ?, ?, ?, ?)
        """, ("Default Admin", "admin@rakshanet.local", "admin", pw_hash, "SOC"))
        conn.commit()
        print("User admin@rakshanet.local created successfully.")
    else:
        print("User already exists.")
    conn.close()

if __name__ == "__main__":
    seed_user()
