import mysql.connector
import sys
import traceback
import os
from dotenv import load_dotenv

load_dotenv()

# Extract components from DATABASE_URL or use defaults
user = "pnj_admin"
password = "PtLJjyOWuG_/.8b@"
host = "localhost"
database = "bkxatnkyyu"

try:
    print(f"Connecting to {database} on {host} as {user}...")
    conn = mysql.connector.connect(
        user=user,
        password=password,
        host=host,
        database=database
    )
    print("Connection SUCCESSFUL!")
    cursor = conn.cursor()
    cursor.execute("SELECT 1")
    print(f"Query Result: {cursor.fetchone()}")
    conn.close()
except Exception as e:
    print(f"Connection FAILED: {str(e)}")
    print(f"Exception type: {type(e)}")
    traceback.print_exc()
    sys.exit(1)
