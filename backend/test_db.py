from app.database import engine
from sqlalchemy import text
import sys

import traceback

try:
    with engine.connect() as conn:
        res = conn.execute(text("SELECT 1"))
        print(f"DB Connection OK: {res.fetchone()}")
except Exception as e:
    print(f"DB Connection FAILED: {str(e)}")
    print(f"Exception type: {type(e)}")
    print(f"Exception args: {e.args}")
    traceback.print_exc()
    sys.exit(1)
