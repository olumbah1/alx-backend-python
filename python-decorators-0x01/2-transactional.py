import sqlite3 
import functools

def with_db_connection(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        conn = sqlite3.connect('users.db')
        try:
            return func(conn, *args, **kwargs)
        finally:
            conn.close()
    return wrapper

def transactional(func):
    @functools.wraps(func)
    def wrapper(conn, *args, **kwargs):
        try:
            result = func(conn, *args, **kwargs)
            conn.commit()  # Commit if successful
            return result
        except Exception as e:
            conn.rollback()  # Rollback on error
            print(f"[TRANSACTION ERROR] Rolled back due to: {e}")
            raise
    return wrapper
           

# Function using both decorators
@with_db_connection
@transactional
def update_user_email(conn, user_id, new_email):
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET email = ? WHERE id = ?", (new_email, user_id))

# Example usage
update_user_email(user_id=1, new_email='Crawford_Cartwright@hotmail.com')