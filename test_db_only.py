from db_handler import get_db_connection

def test_connection():
    print("🔌 Testing connection to AWS RDS...")
    
    conn = get_db_connection()
    
    if conn:
        print("✅ SUCCESS! Connection established.")
        
        # בונוס: נבדוק גם שיש גישה לטבלאות
        try:
            cur = conn.cursor()
            cur.execute("SELECT count(*) FROM users;")
            count = cur.fetchone()[0]
            print(f"📊 Database is reachable. Current users count: {count}")
            cur.close()
            conn.close()
            print("🔒 Connection closed safely.")
        except Exception as e:
            print(f"⚠️ Connection worked, but query failed: {e}")
    else:
        print("❌ FAILURE: Could not connect. Check your password in db_handler.py")

if __name__ == "__main__":
    test_connection()