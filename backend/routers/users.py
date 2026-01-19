from fastapi import APIRouter, HTTPException
import pandas as pd
from db_handler import get_db_connection

router = APIRouter()

@router.get("/users")
def get_users():
    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="DB Connection Failed - Check environment variables (DB_PASS, DB_HOST, etc.)")
    try:
        df = pd.read_sql("SELECT user_id, full_name, is_pregnant, gender FROM users ORDER BY user_id", conn)
        return df.to_dict(orient="records")
    except Exception as e:
        print(f"Error in get_users: {e}")
        raise HTTPException(status_code=500, detail=f"Error fetching users: {str(e)}")
    finally:
        if conn:
            conn.close()
