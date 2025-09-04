import sys
import os
from itertools import islice

# Add current directory to Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

try:
    # Import the module
    stream_users_module = __import__('0-stream_users')
    
    # Get the function from the module
    stream_users = stream_users_module.stream_users
    
    # Iterate over the generator function and print only the first 6 rows
    for user in islice(stream_users(), 6):
        print(user)
        
except ImportError as e:
    print(f"Import error: {e}")
    print("Make sure '0-stream_users.py' exists in the same directory")
except Exception as e:
    print(f"Error: {e}")