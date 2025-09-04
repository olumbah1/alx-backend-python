#!/usr/bin/python3
import os
from dotenv import load_dotenv

def debug_env():
    """Debug environment variable loading"""
    
    print("Environment Variable Debug")
    print("=" * 40)
    
    # Check if .env file exists
    env_file_path = ".env"
    if os.path.exists(env_file_path):
        print(f"✅ .env file found at: {os.path.abspath(env_file_path)}")
        
        # Read and display .env file contents (safely)
        print("\n📄 .env file contents:")
        with open(env_file_path, 'r') as f:
            lines = f.readlines()
            for i, line in enumerate(lines, 1):
                line = line.strip()
                if line and not line.startswith('#'):
                    key = line.split('=')[0]
                    print(f"Line {i}: {key}=***")  # Hide actual values
                else:
                    print(f"Line {i}: {line}")
    else:
        print(f"❌ .env file NOT found at: {os.path.abspath(env_file_path)}")
        print("Current working directory:", os.getcwd())
        print("Files in current directory:", os.listdir('.'))
        return
    
    print("\n🔄 Loading .env file...")
    load_result = load_dotenv()
    print(f"load_dotenv() returned: {load_result}")
    
    # Check environment variables
    print("\n🔍 Environment Variables:")
    env_vars = ['DB_HOST', 'DB_NAME', 'DB_USER', 'DB_PASSWORD']
    
    for var in env_vars:
        value = os.getenv(var)
        if value is not None:
            if var == 'DB_PASSWORD':
                print(f"{var}: {'*' * len(value)} (length: {len(value)})")
            else:
                print(f"{var}: {value}")
        else:
            print(f"{var}: NOT SET")
    
    print("\n📋 All environment variables containing 'DB':")
    for key, value in os.environ.items():
        if 'DB' in key.upper():
            if 'PASSWORD' in key.upper():
                print(f"{key}: {'*' * len(value)}")
            else:
                print(f"{key}: {value}")

if __name__ == "__main__":
    debug_env()