import psycopg2
import re
import json
import os

# --- פרטי התחברות ---
DB_HOST = os.getenv("DB_HOST", "database-1.cmtkkqyiagdy.us-east-1.rds.amazonaws.com")
DB_NAME = os.getenv("DB_NAME", "postgres")
DB_USER = os.getenv("DB_USER", "postgres")
# ⚠️ WARNING: Fallback password only for testing. In production, always use environment variables!
DB_PASS = os.getenv("DB_PASS", os.getenv("DATABASE_PASSWORD", "Karina1256"))  # Fallback for testing only 

def get_db_connection():
    if not DB_PASS:
        print("❌ Error: DB_PASS environment variable is not set!")
        return None
    try:
        conn = psycopg2.connect(
            host=DB_HOST,
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASS,
            sslmode='require'
        )
        return conn
    except Exception as e:
        print(f"❌ Error connecting to DB: {e}")
        return None

def repair_json_string(text):
    """
    פונקציית קסם: מתקנת שגיאות נפוצות של ה-AI ב-JSON
    """
    # תיקון 1: הוספת גרשיים חסרים בהתחלה (כמו במקרה של ה-phosphorus)
    # מחפש: : 476 mg", ומחליף ב: : "476 mg",
    text = re.sub(r':\s*(\d+(?:\.\d+)?\s*[a-zA-Z%]+)(?=")', r': "\1', text)
    
    # תיקון 2: הוספת גרשיים אם חסרים משני הצדדים
    # מחפש: : 476 mg, ומחליף ב: : "476 mg",
    text = re.sub(r':\s*(\d+(?:\.\d+)?\s*[a-zA-Z%]+)(?=[,}])', r': "\1"', text)
    
    return text

def extract_json_from_text(text):
    print("\n🔍 --- DEBUG: מתחיל ניתוח וניקוי טקסט ---")
    
    # שלב א': מציאת הסוגריים המסולסלים
    start_index = text.find('{')
    end_index = text.rfind('}')
    
    if start_index == -1 or end_index == -1:
        print("❌ לא נמצאו סוגריים מסולסלים JSON בטקסט.")
        return None
        
    clean_json = text[start_index : end_index + 1]
    
    # שלב ב': הפעלת התיקון האוטומטי
    fixed_json = repair_json_string(clean_json)
    
    try:
        # נסיון המרה
        return json.loads(fixed_json)
    except json.JSONDecodeError as e:
        print(f"⚠️ נכשל בנסיון ראשון, מנסה ניקוי אגרסיבי יותר... ({e})")
        # לפעמים יש בעיות עם שורות חדשות
        fixed_json = fixed_json.replace('\n', ' ')
        try:
            return json.loads(fixed_json)
        except:
            print(f"❌ שגיאה סופית בפענוח ה-JSON.\nהנה הטקסט הבעייתי:\n{fixed_json[:200]}...")
            return None

def parse_quantity(value_str):
    if not isinstance(value_str, str):
        # אם ה-AI החזיר מספר במקום טקסט (למשל 500 במקום "500 mg")
        if isinstance(value_str, (int, float)):
            return float(value_str), "unknown"
        return 0, ""
        
    clean_str = str(value_str).strip()
    match = re.match(r"([\d\.]+)\s*([a-zA-Z]+)", clean_str)
    if match:
        return float(match.group(1)), match.group(2).lower()
    return 0, ""

def save_meal_to_db(user_id, image_url, ai_json_text):
    print(f"🚀 Database Save Started - User: {user_id}, URL: {image_url}")
    conn = get_db_connection()
    if not conn:
        return
    try:
        # כאן אנחנו משתמשים ב-ai_json_text שקיבלנו
        data = extract_json_from_text(ai_json_text)
        if not data:
            return
        
        cur = conn.cursor()
        summary = data.get('overall_analysis', 'No summary')

        cur.execute("""
            INSERT INTO meals (user_id, image_url, ai_analysis_summary)
            VALUES (%s, %s, %s) RETURNING meal_id;
        """, (user_id, image_url, summary))

        meal_id = cur.fetchone()[0]
        print(f"💾 ארוחה נשמרה! (ID: {meal_id})")
        
        # 2. Items
        items = data.get('items', [])
        for item in items:
            food_name = item.get('food_name', 'Unknown')
            weight = item.get('estimated_weight_grams', 0)
            macros = item.get('macros', {})
            
            cur.execute("""
                INSERT INTO food_items (meal_id, food_name, estimated_weight_g, calories_kcal, protein_g, carbs_g, fat_g)
                VALUES (%s, %s, %s, %s, %s, %s, %s) RETURNING item_id;
            """, (meal_id, food_name, weight, macros.get('calories', 0), macros.get('protein', 0), macros.get('carbs', 0), macros.get('fat', 0)))
            item_id = cur.fetchone()[0]

            # 3. Micros
            micros = item.get('micros', {})
            count = 0
            for k, v in micros.items():
                amount, unit = parse_quantity(v)
                if amount > 0:
                    cur.execute("""
                        INSERT INTO consumed_micros (item_id, nutrient_name, amount, unit)
                        VALUES (%s, %s, %s, %s);
                    """, (item_id, k, amount, unit))
                    count += 1
            print(f"   > {food_name}: נשמרו {count} ויטמינים.")

        conn.commit()
        print("✅ הכל נשמר בהצלחה!")
        
    except Exception as e:
        print(f"❌ שגיאה בשמירה: {e}")
        if conn: conn.rollback()
    finally:
        if conn: conn.close()