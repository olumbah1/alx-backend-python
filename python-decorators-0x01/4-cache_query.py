import time
import sqlite3 
import functools

# Global query cache dictionary
query_cache = {}

# Decorator to open and close DB connection
def with_db_connection(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        conn = sqlite3.connect('users.db')
        try:
            return func(conn, *args, **kwargs)
        finally:
            conn.close()
    return wrapper

# Decorator to cache SQL query results
def cache_query(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        query = kwargs.get("query") or (args[1] if len(args) > 1 else None)
        if query in query_cache:
            print(f"[CACHE] Returning cached result for query: {query}")
            return query_cache[query]
        print(f"[DB] Executing and caching result for query: {query}")
        result = func(*args, **kwargs)
        query_cache[query] = result
        return result
    return wrapper

# Function to fetch users with caching and DB connection
@with_db_connection
@cache_query
def fetch_users_with_cache(conn, query):
    cursor = conn.cursor()
    cursor.execute(query)
    return cursor.fetchall()

# First call: goes to DB
users = fetch_users_with_cache(query="SELECT * FROM users")

# Second call: uses cache
users_again = fetch_users_with_cache(query="SELECT * FROM users")
