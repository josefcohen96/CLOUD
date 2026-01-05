# import psycopg2
# from db_handler import get_db_connection

# def generate_daily_report(user_id):
#     conn = get_db_connection()
#     if not conn:
#         return

#     cur = conn.cursor()

#     # 1. שליפת פרופיל המשתמש
#     print(f"📊 מייצר דוח עבור משתמש: {user_id}...")
    
#     cur.execute("""
#         SELECT 
#             full_name,
#             gender, 
#             (CURRENT_DATE - date_of_birth) / 30 AS age_months,
#             CASE 
#                 WHEN is_pregnant THEN 'pregnancy' 
#                 WHEN is_lactating THEN 'lactation' 
#                 ELSE 'normal' 
#             END as condition
#         FROM users 
#         WHERE user_id = %s
#     """, (user_id,))
    
#     user_profile = cur.fetchone()
#     if not user_profile:
#         print("❌ משתמש לא נמצא.")
#         return

#     full_name, gender, age_months, condition = user_profile
#     print(f"   👤 פרופיל: {full_name} | מין: {gender} | גיל: {int(age_months/12)} שנים ({age_months} חודשים) | מצב: {condition}")

#     # 2. השאילתה - JOIN בין מה שנאכל לתקן
#     # שים לב: עכשיו ההתאמה היא מושלמת כי שני הצדדים הם snake_case
#     query = """
#     WITH daily_intake AS (
#         SELECT 
#             cm.nutrient_name,
#             SUM(cm.amount) as total_consumed,
#             MAX(cm.unit) as unit
#         FROM consumed_micros cm
#         JOIN food_items fi ON cm.item_id = fi.item_id
#         JOIN meals m ON fi.meal_id = m.meal_id
#         WHERE m.user_id = %s 
#           AND m.created_at::date = CURRENT_DATE
#         GROUP BY cm.nutrient_name
#     )
#     SELECT 
#         di.nutrient_name,
#         di.total_consumed,
#         ns.daily_value as target_value,
#         di.unit,
#         (di.total_consumed / ns.daily_value) * 100 as percentage_fulfilled
#     FROM daily_intake di
#     JOIN nutrient_standards ns ON di.nutrient_name = ns.nutrient_name
#     WHERE 
#         ns.gender IN (%s, 'both')
#         AND ns.min_age_months <= %s 
#         AND ns.max_age_months >= %s
#         AND ns.condition = %s
#     ORDER BY percentage_fulfilled ASC;
#     """

#     cur.execute(query, (user_id, gender, age_months, age_months, condition))
#     results = cur.fetchall()

#     if not results:
#         print("\n⚠️ לא נמצאו נתונים להשוואה. האם הרצת את ה-AI היום עבור המשתמש הזה?")
#         return

#     # 3. הדפסת הדוח
#     print("\n" + "="*85)
#     print(f"🥗 דוח תזונה קליני - {full_name}")
#     print("="*85)
#     print(f"{'רכיב תזונתי':<25} | {'נצרך':<12} | {'יעד יומי':<12} | {'סטטוס (טווח 10%+-)'}")
#     print("-" * 85)

#     for row in results:
#         nutrient_raw, consumed, target, unit, percent = row
        
#         # המרה יפה להדפסה: 'vitamin_B12' -> 'Vitamin B12'
#         nutrient_display = nutrient_raw.replace('_', ' ').title().replace('B12', 'B12').replace('Iu', 'IU')

#         # לוגיקה: טווח תקין בין 90% ל-110%
#         if percent < 90:
#             status = "🔴 חוסר"
#             diff = f"(חסרים {target - consumed:.1f}{unit})"
#         elif 90 <= percent <= 110:
#             status = "🟢 תקין"
#             diff = "✅"
#         else: # מעל 110%
#             status = "🔵 עודף"
#             diff = f"(+{consumed - target:.1f}{unit})"

#         print(f"{nutrient_display:<25} | {float(consumed):.1f} {unit:<4} | {float(target):.1f} {unit:<4} | {status} {int(percent)}% {diff}")

#     print("="*85 + "\n")

#     cur.close()
#     conn.close()

# if __name__ == "__main__":
#     # וודא שאתה מריץ על אותו ID ששמרת ב-nutrition_ai.py
#     # כרגע נבדוק את יוסי (1)
#     generate_daily_report(1)