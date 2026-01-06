from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from mangum import Mangum
import shutil
import os
import pandas as pd
import json
import boto3
import uuid
from db_handler import get_db_connection
from nutrition_ai import analyze_food_image
from recommender_engine import recommend_food

app = FastAPI(root_path="/default")

# אפשור גישה מה-Frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# הגדרת S3 - החלף לשם הבאקט שלך
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
                ContentType="image/jpeg",
                ACL='public-read' 
            )
        return f"https://{S3_BUCKET}.s3.amazonaws.com/{unique_name}"
    except Exception as e:
        print(f"❌ S3 ERROR: {e}")
        return None
    
@app.get("/users")
def get_users():
    conn = get_db_connection()
    if not conn: raise HTTPException(status_code=500, detail="DB Connection Failed")
    try:
        df = pd.read_sql("SELECT user_id, full_name, is_pregnant, gender FROM users ORDER BY user_id", conn)
        return df.to_dict(orient="records")
    finally: conn.close()

@app.post("/analyze")
async def analyze_meal_endpoint(user_id: int = Form(...), file: UploadFile = File(...)):
    temp_filename = f"/tmp/{file.filename}"
    if os.name == 'nt': temp_filename = file.filename 

    try:
        # שמירת הקובץ זמנית בשרת/למבדה
        with open(temp_filename, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # 1. העלאה ל-S3 וקבלת URL
        image_url = upload_to_s3(temp_filename, file.filename)
        
        # 2. שליחה לניתוח AI (כולל ה-URL לשמירה ב-DB)
        analysis_result = analyze_food_image(temp_filename, user_id=user_id, image_url=image_url)
        
        if not analysis_result: 
            raise HTTPException(status_code=500, detail="Analysis failed")
            
        return {"status": "success", "data": analysis_result, "image_url": image_url}

    finally:
        if os.path.exists(temp_filename): 
            os.remove(temp_filename)

@app.get("/report/{user_id}")
def get_report(user_id: int):
    conn = get_db_connection()
    if not conn: raise HTTPException(status_code=500, detail="DB Error")
    try:
        user_query = "SELECT gender, (CURRENT_DATE - date_of_birth)/30, CASE WHEN is_pregnant THEN 'pregnancy' ELSE 'normal' END FROM users WHERE user_id = %s"
        cur = conn.cursor()
        cur.execute(user_query, (user_id,))
        prof = cur.fetchone()
        if not prof: return {"error": "User not found"}
        gender, age_months, condition = prof
        
        query = """
WITH latest_meal AS (
    SELECT meal_id, ai_analysis_summary, created_at, image_url 
    FROM meals WHERE user_id = %s ORDER BY created_at DESC LIMIT 1
),
meal_intake AS (
    SELECT cm.nutrient_name, SUM(cm.amount) as total_consumed, MAX(cm.unit) as unit
    FROM consumed_micros cm
    JOIN food_items fi ON cm.item_id = fi.item_id
    JOIN latest_meal lm ON fi.meal_id = lm.meal_id
    GROUP BY cm.nutrient_name
)
SELECT mi.nutrient_name, mi.total_consumed, ns.daily_value as target_value, 
       mi.unit, (mi.total_consumed / ns.daily_value)*100 as percentage
FROM meal_intake mi
JOIN nutrient_standards ns ON LOWER(mi.nutrient_name) = LOWER(ns.nutrient_name)
WHERE ns.gender IN (%s, 'both') 
  AND ns.min_age_months <= %s 
  AND ns.max_age_months >= %s 
  AND ns.condition = %s
ORDER BY percentage ASC
"""
        df = pd.read_sql(query, conn, params=(user_id, gender, age_months, age_months, condition))
        report_data = df.to_dict(orient="records")
        
        # שליפת הסיכום והתמונה מהארוחה האחרונה
        summary_query = "SELECT ai_analysis_summary, image_url FROM meals WHERE user_id = %s ORDER BY created_at DESC LIMIT 1"
        summary_df = pd.read_sql(summary_query, conn, params=(user_id,))
        
        summary_text = summary_df.iloc[0]['ai_analysis_summary'] if not summary_df.empty else ""
        image_url = summary_df.iloc[0]['image_url'] if not summary_df.empty else None
        
        return {"report": report_data, "summary": summary_text, "image_url": image_url}
    finally: conn.close()

@app.get("/recommendations/{user_id}")
def get_recommendations_endpoint(user_id: int):
    return recommend_food(user_id)

@app.get("/history/{user_id}")
def get_meal_history(user_id: int):
    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="DB Connection Failed")
    try:
        # שליפת הארוחות כולל ה-URL של התמונה
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