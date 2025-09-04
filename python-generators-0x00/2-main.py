import sys
import os

# Add current directory to Python path to ensure imports work
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

try:
    processing = __import__('1-batch_processing')
    
    # print processed users in a batch of 10 (since you have only 10 datasets)
    for batch in processing.batch_processing(10):
        for user in batch:
            print(user)
except ImportError as e:
    print(f"Import error: {e}")
    print("Make sure '1-batch_processing.py' exists in the same directory")
except BrokenPipeError:
    sys.stderr.close()
except Exception as e:
    print(f"Error: {e}")