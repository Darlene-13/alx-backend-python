import sqlite3

def create_users_database():
    # Connect to the database (creates users.db if it doesn't exist)
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()

    # Create users table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT NOT NULL
        )
    ''')

    # Insert sample data for testing
    sample_users = [
        ('alice@example.com',),
        ('bob@example.com',),
        ('charlie@example.com',)
    ]
    cursor.executemany('INSERT OR IGNORE INTO users (email) VALUES (?)', sample_users)

    # Commit changes and close connection
    conn.commit()
    conn.close()
    print("Users database created successfully with sample data.")

if __name__ == "__main__":
    create_users_database()