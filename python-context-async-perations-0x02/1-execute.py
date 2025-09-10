import sqlite3

class ExecuteQuery:
    def __init__(self, query, params=()):
        self.query = query
        self.params = params
        self.conn = None
        self.cursor = None

    def __enter__(self):
        # Open connection and execute the query
        self.conn = sqlite3.connect('users.db')
        self.cursor = self.conn.cursor()
        self.cursor.execute(self.query, self.params)
        return self.cursor.fetchall()  # Return query results

    def __exit__(self, exc_type, exc_val, exc_tb):
        # Close connection safely
        if self.cursor:
            self.cursor.close()
        if self.conn:
            self.conn.close()


# Usage Example
query = "SELECT * FROM users WHERE age > ?"
params = (25,)

with ExecuteQuery(query, params) as result:
    print("Users older than 25:")
    for row in result:
        print(row)