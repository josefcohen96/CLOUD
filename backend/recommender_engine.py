import pandas as pd
from db_handler import get_db_connection

# === המיפוי המלא והמעודכן (תואם ל-SQL החדש) ===
NUTRIENT_MAP = {
    # ויטמינים
    'vitamin_a': 'vitamin_a_mcg',
    'vitamin_c': 'vitamin_c_mg',
    'vitamin_d': 'vitamin_d_mcg',
    'vitamin_e': 'vitamin_e_mg',
    'vitamin_k': 'vitamin_k_mcg',
    'thiamin_b1': 'vitamin_b1_mg',
    'riboflavin_b2': 'vitamin_b2_mg',
    'niacin_b3': 'vitamin_b3_mg',
    'vitamin_b6': 'vitamin_b6_mg',
    'vitamin_b12': 'vitamin_b12_mcg',
    'folate': 'folate_mcg',
    
    # מינרלים
    'calcium': 'calcium_mg',
    'iron': 'iron_mg',
    'magnesium': 'magnesium_mg',
    'phosphorus': 'phosphorus_mg',
    'potassium': 'potassium_mg',
    'sodium': 'sodium_mg',
    'zinc': 'zinc_mg'
}

def get_deficiency_amounts(user_id):
    """מחשב כמה בדיוק חסר למשתמש מכל רכיב"""
    conn = get_db_connection()
    
    # 1. שליפת פרופיל
    user_query = "SELECT gender, (CURRENT_DATE - date_of_birth) / 30, CASE WHEN is_pregnant THEN 'pregnancy' WHEN is_lactating THEN 'lactation' ELSE 'normal' END FROM users WHERE user_id = %s"
    cur = conn.cursor()
    cur.execute(user_query, (user_id,))
    prof = cur.fetchone()
    if not prof: 
        conn.close()
        return {}
    gender, age_months, condition = prof
    
    # 2. שליפת צריכה יומית מול יעד
    query = """
    WITH daily_sum AS (
        SELECT cm.nutrient_name, SUM(cm.amount) as consumed
        FROM consumed_micros cm
        JOIN food_items fi ON cm.item_id = fi.item_id
        JOIN meals m ON fi.meal_id = m.meal_id
        WHERE m.user_id = %s AND m.created_at::date = CURRENT_DATE
        GROUP BY cm.nutrient_name
    )
    SELECT 
        ns.nutrient_name,
        COALESCE(ds.consumed, 0) as consumed,
        ns.daily_value as target
    FROM nutrient_standards ns
    LEFT JOIN daily_sum ds ON ns.nutrient_name = ds.nutrient_name
    WHERE ns.gender IN (%s, 'both') 
      AND ns.min_age_months <= %s 
      AND ns.max_age_months >= %s
      AND ns.condition = %s
    """
    
    df = pd.read_sql(query, conn, params=(user_id, gender, age_months, age_months, condition))
    conn.close()
    
    deficiencies = {}
    for _, row in df.iterrows():
        consumed = row['consumed']
        target = row['target']
        
        # אם יש חוסר (פחות מ-100%)
        if target > 0 and consumed < target:
            missing_val = target - consumed
            # מנרמלים את השם (למשל 'Vitamin A' -> 'vitamin_a')
            key = row['nutrient_name'].lower().replace(' ', '_')
            
            if key in NUTRIENT_MAP:
                db_col = NUTRIENT_MAP[key]
                deficiencies[db_col] = missing_val

    return deficiencies

def recommend_food(user_id, max_items=3):
    """האלגוריתם החמדן האיטרטיבי"""
    current_gaps = get_deficiency_amounts(user_id)
    if not current_gaps:
        return []

    conn = get_db_connection()
    foods_df = pd.read_sql("SELECT * FROM recommendation_foods", conn)
    conn.close()
    
    recommended_list = []
    
    for _ in range(max_items):
        if not current_gaps: break

        best_food = None
        best_score = -1
        best_reason = ""
        
        for idx, food in foods_df.iterrows():
            if food['food_name'] in [r['food_name'] for r in recommended_list]:
                continue
                
            score = 0
            impacts = []
            for nutrient_col, missing_amount in current_gaps.items():
                food_amount = food[nutrient_col]
                if food_amount > 0:
                    covered = min(food_amount, missing_amount)
                    # ניקוד: אחוז הכיסוי של החוסר
                    importance = (covered / missing_amount) * 100
                    score += importance
                    
                    if importance > 15: # רק אם זה תורם משמעותית
                        # === התיקון מתחיל כאן ===
                        # במקום לקחת רק את המילה הראשונה, ניקח את הכל חוץ מהסוף (היחידה)
                        # דוגמה: 'vitamin_a_mcg' -> נפרק ל-['vitamin', 'a', 'mcg'] -> ניקח ['vitamin', 'a']
                        parts = nutrient_col.split('_')
                        clean_parts = parts[:-1] 
                        clean_name = " ".join(clean_parts).title() # יהפוך ל-"Vitamin A"
                        # === סוף התיקון ===
                        
                        impacts.append(f"{clean_name} ({int(importance)}%)")
            
            # פקטור יעילות: ניקוד חלקי קלוריות
            final_score = score / (food['calories'] + 10)
            
            if final_score > best_score:
                best_score = final_score
                best_food = food
                best_reason = ", ".join(impacts[:3])

        if best_food is not None and best_score > 0.5:
            recommended_list.append({
                "food_name": best_food['food_name'],
                "calories": best_food['calories'],
                "serving": f"{best_food['serving_grams']}g",
                "reason": best_reason,
                "tags": best_food['tags']
            })
            
            # עדכון חוסרים לסיבוב הבא
            keys_to_remove = []
            for nutrient in current_gaps:
                provided = best_food[nutrient]
                current_gaps[nutrient] -= provided
                if current_gaps[nutrient] <= 0:
                    keys_to_remove.append(nutrient)
            
            for k in keys_to_remove: del current_gaps[k]
        else:
            break

    return recommended_list