import redis
import os
import json

# הגדרת הכתובת - אותה תכניס ב-Environment Variables ב-Lambda/GitHub
REDIS_HOST = os.getenv("REDIS_HOST")
REDIS_PORT = 6379

# יצירת חיבור (Connection Pool)
try:
    cache_client = redis.Redis(
        host=REDIS_HOST,
        port=REDIS_PORT,
        decode_responses=True,
        socket_connect_timeout=2  # מניעת תקיעה של הלמבדה אם ה-Cache לא זמין
    )
except Exception as e:
    print(f"Cache connection error: {e}")
    cache_client = None

def get_cached_nutrition(food_text: str):
    """שליפת נתונים מה-Cache במידה וקיימים"""
    if not cache_client:
        return None
    try:
        data = cache_client.get(food_text)
        return json.loads(data) if data else None
    except Exception:
        return None

def set_nutrition_cache(food_text: str, nutrition_data: dict, expire_hours=24):
    """שמירת נתוני ניתוח ב-Cache עם זמן תפוגה"""
    if not cache_client:
        return
    try:
        # שמירה ל-24 שעות כדי לחסוך קריאות AI חוזרות
        cache_client.setex(
            food_text,
            expire_hours * 3600,
            json.dumps(nutrition_data)
        )
    except Exception as e:
        print(f"Error saving to cache: {e}")