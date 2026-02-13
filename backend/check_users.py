from app.supabase_client import supabase
import json

def check_id_5():
    res = supabase.table("users").select("*").eq("id", 5).execute()
    print("USER ID 5 DETAILS:")
    print(json.dumps(res.data, indent=2))

if __name__ == "__main__":
    check_id_5()
