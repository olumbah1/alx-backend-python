Create 
Proper Function Structure

All required functions:
connect_db(),
create_database(),
connect_to_prodev(),
create_table(), 
insert_data()

SQL Syntax:

VARCHAR (not VACHAR)
INT for age (simpler than DECIMAL for whole numbers)
VARCHAR(36) for UUID (proper size)
Proper INDEX syntax

Database Schema:
sqlCREATE TABLE IF NOT EXISTS user_data (
    user_id VARCHAR(36) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    email VARCHAR(255) NOT NULL,
    age INT NOT NULL,
    INDEX idx_user_id (user_id)
)
Error Handling:

Try-catch blocks for all database operations
Proper connection management
File handling for CSV reading

CSV Data Processing:

Reads the CSV file properly
Checks for duplicate entries before inserting
Uses parameterized queries to prevent SQL injection

How to Use:
Save this as seed.py
Added password in both connection functions
Make sure user_data.csv is in the same directory
Run the test: ./0-main.py