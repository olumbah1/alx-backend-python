#!/usr/bin/python3

import mysql.connector
import csv
import uuid
from mysql.connector import Error

def connect_db():
    """
    Connects to the MySQL database server
    Returns: connection object or None if failed
    """
    try:
        connection = mysql.connector.connect(
            host='localhost',
            user='root',
            password='Olumide'  
        )
        if connection.is_connected():
            print("Successfully connected to MySQL server")
            return connection
    except Error as e:
        print(f"Error connecting to MySQL: {e}")
        return None

def create_database(connection):
    """
    Creates the database ALX_prodev if it does not exist
    """
    try:
        cursor = connection.cursor()
        cursor.execute("CREATE DATABASE IF NOT EXISTS ALX_prodev")
        print("Database ALX_prodev created successfully (or already exists)")
        cursor.close()
    except Error as e:
        print(f"Error creating database: {e}")

def connect_to_prodev():
    """
    Connects to the ALX_prodev database in MySQL
    Returns: connection object or None if failed
    """
    try:
        connection = mysql.connector.connect(
            host='localhost',
            user='root',
            password='Olumide',  
            database='ALX_prodev'
        )
        if connection.is_connected():
            print("Successfully connected to ALX_prodev database")
            return connection
    except Error as e:
        print(f"Error connecting to ALX_prodev database: {e}")
        return None

def create_table(connection):
    """
    Creates a table user_data if it does not exist with the required fields
    """
    try:
        cursor = connection.cursor()
        
        # Create table with proper MySQL syntax
        create_table_query = """
        CREATE TABLE IF NOT EXISTS user_data (
            user_id VARCHAR(36) PRIMARY KEY,
            name VARCHAR(255) NOT NULL,
            email VARCHAR(255) NOT NULL,
            age INT NOT NULL,
            INDEX idx_user_id (user_id)
        )
        """
        
        cursor.execute(create_table_query)
        print("Table user_data created successfully")
        cursor.close()
        
    except Error as e:
        print(f"Error creating table: {e}")

def insert_data(connection, csv_file):
    """
    Inserts data from CSV file into the database if it does not exist
    """
    try:
        cursor = connection.cursor()
        
        # Read CSV file and insert data
        with open(csv_file, 'r', newline='', encoding='utf-8') as file:
            csv_reader = csv.DictReader(file)
            
            for row in csv_reader:
                # Check if user already exists
                check_query = "SELECT user_id FROM user_data WHERE user_id = %s"
                cursor.execute(check_query, (row['user_id'],))
                
                if cursor.fetchone() is None:
                    # Insert new user
                    insert_query = """
                    INSERT INTO user_data (user_id, name, email, age)
                    VALUES (%s, %s, %s, %s)
                    """
                    cursor.execute(insert_query, (
                        row['user_id'],
                        row['name'],
                        row['email'],
                        int(row['age'])
                    ))
        
        # Commit the changes
        connection.commit()
        print(f"Data from {csv_file} inserted successfully")
        cursor.close()
        
    except Error as e:
        print(f"Error inserting data: {e}")
        connection.rollback()
    except FileNotFoundError:
        print(f"CSV file {csv_file} not found")
    except Exception as e:
        print(f"Unexpected error: {e}")

# Test the functions (optional - remove if not needed)
if __name__ == "__main__":
    # Test connection
    conn = connect_db()
    if conn:
        create_database(conn)
        conn.close()
        
        # Connect to the specific database
        prodev_conn = connect_to_prodev()
        if prodev_conn:
            create_table(prodev_conn)
            insert_data(prodev_conn, 'user_data.csv')
            prodev_conn.close()