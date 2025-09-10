import sqlite3

# 🔹 Custom context manager class
class DatabaseConnection:
    def __init__(self, db_name):
        self.db_name = db_name
        self.conn = None

    def __enter__(self):
        self.conn = sqlite3.connect(self.db_name)
        return self.conn

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.conn:
            self.conn.close()

# 🔹 Using the context manager to execute a query
with DatabaseConnection('users.db') as conn:
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users")
    results = cursor.fetchall()
    print("Users:", results)
