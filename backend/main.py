from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from mangum import Mangum
import shutil
import os
import pandas as pd
import json
import boto3
import uuid
import tempfile
from db_handler import get_db_connection
from nutrition_ai import analyze_food_image
from recommender_engine import recommend_food
import hashlib
from cache_handler import get_cached_nutrition, set_nutrition_cache

app = FastAPI(root_path="/default")

# אפשור גישה מה-Frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# הגדרת S3 - וודא ששם הבאקט מעודכן לחשבון הפעיל
S3_BUCKET = "nutrition-app-images"
s3_client = boto3.client('s3')

def upload_to_s3(file_path, original_name):
    unique_name = f"{uuid.uuid4()}-{original_name}"
    try:
        with open(file_path, "rb") as f:
            s3_client.put_object(
                Bucket=S3_BUCKET,
                Key=unique_name,
                Body=f,
                ContentType="image/jpeg"
            )
        return f"https://{S3_BUCKET}.s3.amazonaws.com/{unique_name}"
    
    except Exception as e:
        print(f"❌ S3 ERROR: {e}")
        return None
    
@app.get("/users")
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

@app.post("/analyze")
async def analyze_meal_endpoint(user_id: int = Form(...), file: UploadFile = File(...)):
    # יצירת נתיב זמני בטוח לכל מערכת הפעלה
    if os.name == 'nt':
        temp_dir = os.path.join(os.getenv('TEMP', os.getcwd()), 'nutrition_app')
        os.makedirs(temp_dir, exist_ok=True)
        temp_filename = os.path.join(temp_dir, f"{uuid.uuid4()}_{file.filename}")
    else:
        temp_filename = f"/tmp/{uuid.uuid4()}_{file.filename}"
    print(f"🔍 Starting analysis for user {user_id} and file {file.filename}")
    try:
        # 1. קריאת תוכן הקובץ
        file_content = await file.read()
        
        # 2. יצירת מפתח ייחודי לתמונה (MD5 Hash)
        # file_hash = hashlib.md5(file_content).hexdigest()
        # cache_key = f"img_hash_{file_hash}"

        # # 3. בדיקה ב-Valkey (Redis) אם כבר ניתחנו את התמונה הזו בעבר
        # cached_result = get_cached_nutrition(cache_key)
        # if cached_result:
        #     print(f"Cache Hit for image {file.filename}! Returning results from Valkey.")
        #     return {"status": "success", "data": cached_result, "cached": True}

        # # 4. אם אין ב-Cache - ממשיכים ללוגיקה הרגילה
        # print(f"Cache Miss for {file.filename}. Starting AI analysis...")
        
        # כיוון שקראנו את ה-Stream עם await file.read(), צריך לכתוב אותו לקובץ זמני
        with open(temp_filename, "wb") as buffer:
            buffer.write(file_content)
        
        image_url = upload_to_s3(temp_filename, file.filename)
        print(f"Uploaded image to S3: {image_url}")
        analysis_result = analyze_food_image(temp_filename, user_id=user_id, image_url=image_url)
        print(f"Analysis result: {analysis_result}")
        if not analysis_result: 
            raise HTTPException(status_code=500, detail="Analysis failed")
            
        # 5. שמירת התוצאה ב-Valkey לשימוש עתידי (למשל ל-24 שעות)
        # set_nutrition_cache(cache_key, analysis_result, expire_hours=24)

        return {"status": "success", "data": analysis_result, "image_url": image_url, "cached": False}

    finally:
        # ניקוי הקובץ הזמני
        if os.path.exists(temp_filename): 
            os.remove(temp_filename)

@app.get("/report/{user_id}")
def get_report(user_id: int, meal_id: int = Query(None)):
    conn = get_db_connection()
    if not conn: raise HTTPException(status_code=500, detail="DB Error")
    try:
        cur = conn.cursor()
        # 1. שליפת נתוני משתמש
        cur.execute("SELECT gender, (CURRENT_DATE - date_of_birth)/30, CASE WHEN is_pregnant THEN 'pregnancy' ELSE 'normal' END FROM users WHERE user_id = %s", (user_id,))
        prof = cur.fetchone()
        if not prof:
            raise HTTPException(status_code=404, detail="User not found")
        gender, age_months, condition = prof
        
        # 2. פילטר לפי ארוחה או יום - תיקון SQL Injection
        if meal_id:
            meal_filter = "m.meal_id = %s"
            meal_params = (meal_id,)
        else:
            meal_filter = "m.user_id = %s AND m.created_at::date = CURRENT_DATE"
            meal_params = (user_id,)
        
        # 3. שאילתה שמביאה את כל הרכיבים מהתקן ומצמידה אליהם צריכה (אם יש)
        query = """
        SELECT 
            ns.nutrient_name,
            COALESCE(di.total, 0) as total_consumed,
            ns.daily_value as target_value,
            ns.unit,
            (COALESCE(di.total, 0) / NULLIF(ns.daily_value, 0)) * 100 as percentage
        FROM nutrient_standards ns
        LEFT JOIN (
            SELECT cm.nutrient_name, SUM(cm.amount) as total
            FROM consumed_micros cm
            JOIN food_items fi ON cm.item_id = fi.item_id
            JOIN meals m ON fi.meal_id = m.meal_id
            WHERE """ + meal_filter + """
            GROUP BY cm.nutrient_name
        ) di ON LOWER(ns.nutrient_name) = LOWER(di.nutrient_name)
        WHERE ns.gender IN (%s, 'both') 
          AND ns.min_age_months <= %s AND ns.max_age_months >= %s 
          AND ns.condition = %s
        ORDER BY ns.nutrient_name ASC;
        """
        # שילוב הפרמטרים בצורה בטוחה
        all_params = meal_params + (gender, age_months, age_months, condition)
        report_df = pd.read_sql(query, conn, params=all_params)
        
        # 4. שליפת סיכום ותמונה
        info_query = "SELECT ai_analysis_summary, image_url FROM meals WHERE " + ("meal_id = %s" if meal_id else "user_id = %s ORDER BY created_at DESC LIMIT 1")
        cur.execute(info_query, (meal_id if meal_id else user_id,))
        res = cur.fetchone()
        
        return {
            "report": report_df.to_dict(orient="records"),
            "summary": res[0] if res else "",
            "image_url": res[1] if res else None
        }
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error in get_report: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")
    finally: 
        if conn: conn.close()

@app.get("/recommendations/{user_id}")
def get_recommendations_endpoint(user_id: int):
    return recommend_food(user_id)

@app.get("/history/{user_id}")
def get_meal_history(user_id: int):
    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="DB Connection Failed")
    try:
        query = """
            SELECT meal_id, created_at, ai_analysis_summary, image_url
            FROM meals 
            WHERE user_id = %s 
            ORDER BY created_at DESC
        """
        df = pd.read_sql(query, conn, params=(user_id,))
        df['created_at'] = df['created_at'].astype(str)
        
        return df.to_dict(orient="records")
    finally:
        conn.close()

handler = Mangum(app)