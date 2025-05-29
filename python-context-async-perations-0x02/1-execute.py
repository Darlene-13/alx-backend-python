# python-context-async-perations-0x02/1-execute.py
import sqlite3

class ExecuteQuery:
    def __init__(self, db_name, query, params=()):
        self.db_name = db_name
        self.query = query
        self.params = params
        self.conn = None
        self.cursor = None

    def __enter__(self):
        self.conn = sqlite3.connect(self.db_name)
        self.cursor = self.conn.cursor()
        self.cursor.execute(self.query, self.params)
        return self.cursor.fetchall()

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.conn:
            self.conn.commit()
            self.cursor.close()
            self.conn.close()

def main():
    query = "SELECT * FROM users WHERE age > ?"
    with ExecuteQuery("example.db", query, (25,)) as results:
        for row in results:
            print(row)

if __name__ == "__main__":
    main()