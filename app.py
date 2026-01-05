import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import os
from db_handler import get_db_connection
from recommender_engine import recommend_food
from nutrition_ai import analyze_food_image # ייבוא פונקציית ה-AI

# --- Page Config ---
st.set_page_config(page_title="Clinical Nutrition AI", layout="wide", page_icon="🥗")

# --- Custom CSS for English Layout ---
# --- Custom CSS for Layout ---
st.markdown("""
<style>
    /* עיצוב הכרטיסייה עצמה */
    div[data-testid="stMetric"] {
        background-color: #f0f2f6; /* רקע אפור בהיר */
        border: 1px solid #d6d6d6;
        padding: 15px;
        border-radius: 10px;
        box-shadow: 2px 2px 5px rgba(0,0,0,0.1);
    }

    /* תיקון קריטי: צבע הכותרת של המדד (למשל Iron Coverage) */
    div[data-testid="stMetric"] label {
        color: #333333 !important;
    }

    /* תיקון קריטי: צבע המספר עצמו (למשל 14%) */
    div[data-testid="stMetric"] div[data-testid="stMetricValue"] {
        color: #000000 !important;
    }
</style>
""", unsafe_allow_html=True)

# --- Data Functions ---
def get_user_list():
    conn = get_db_connection()
    df = pd.read_sql("SELECT user_id, full_name, gender, is_pregnant FROM users ORDER BY user_id", conn)
    conn.close()
    return df

def get_latest_meal_analysis(user_id):
    conn = get_db_connection()
    
    # Get Profile
    user_query = "SELECT gender, (CURRENT_DATE - date_of_birth)/30, CASE WHEN is_pregnant THEN 'pregnancy' ELSE 'normal' END FROM users WHERE user_id = %s"
    cur = conn.cursor()
    cur.execute(user_query, (user_id,))
    prof = cur.fetchone()
    if not prof: 
        conn.close()
        return None, None
    gender, age_months, condition = prof
    
    # Get Nutrition Data
    query = """
    WITH latest_meal AS (
        SELECT meal_id, ai_analysis_summary, created_at FROM meals WHERE user_id = %s ORDER BY created_at DESC LIMIT 1
    ),
    meal_intake AS (
        SELECT cm.nutrient_name, SUM(cm.amount) as total_consumed, MAX(cm.unit) as unit
        FROM consumed_micros cm
        JOIN food_items fi ON cm.item_id = fi.item_id
        JOIN latest_meal lm ON fi.meal_id = lm.meal_id
        GROUP BY cm.nutrient_name
    )
    SELECT mi.nutrient_name, mi.total_consumed, ns.daily_value as target_value, mi.unit, (mi.total_consumed / ns.daily_value)*100 as percentage
    FROM meal_intake mi
    JOIN nutrient_standards ns ON mi.nutrient_name = ns.nutrient_name
    WHERE ns.gender IN (%s, 'both') AND ns.min_age_months <= %s AND ns.max_age_months >= %s AND ns.condition = %s
    ORDER BY percentage ASC
    """
    df = pd.read_sql(query, conn, params=(user_id, gender, age_months, age_months, condition))
    
    # Get Meal Summary
    meal_info = pd.read_sql("SELECT ai_analysis_summary, created_at FROM meals WHERE user_id = %s ORDER BY created_at DESC LIMIT 1", conn, params=(user_id,))
    
    conn.close()
    return df, meal_info

# --- Sidebar: User Selection & Upload ---
st.sidebar.image("https://cdn-icons-png.flaticon.com/512/3074/3074063.png", width=80)
st.sidebar.title("Clinical AI Dietitian")

# 1. User Selection
st.sidebar.subheader("1. Select Patient")
users = get_user_list()
user_map = {f"{row['full_name']} ({'Pregnant' if row['is_pregnant'] else row['gender']})": row['user_id'] for _, row in users.iterrows()}
selected_user_label = st.sidebar.selectbox("Patient Profile:", list(user_map.keys()))
selected_user_id = user_map[selected_user_label]

st.sidebar.divider()

# 2. Live Image Upload
st.sidebar.subheader("2. Analyze New Meal")
uploaded_file = st.sidebar.file_uploader("Upload food image", type=['jpg', 'jpeg', 'png'])

if uploaded_file is not None:
    # הצגת תצוגה מקדימה של התמונה
    st.sidebar.image(uploaded_file, caption="Preview", use_container_width=True)
    
    if st.sidebar.button("⚡ Analyze with AI", type="primary"):
        with st.spinner("Processing image with AWS Bedrock..."):
            # שמירה זמנית של הקובץ כדי שהסקריפט יוכל לקרוא אותו
            temp_filename = "temp_upload.jpg"
            with open(temp_filename, "wb") as f:
                f.write(uploaded_file.getbuffer())
            
            # קריאה לפונקציית ה-AI (עם המשתמש הנבחר!)
            result = analyze_food_image(temp_filename, user_id=selected_user_id)
            
            if result:
                st.sidebar.success("Analysis Complete! Refreshing...")
                # מחיקת הקובץ הזמני
                if os.path.exists(temp_filename):
                    os.remove(temp_filename)
                st.rerun() # רענון הדף כדי להציג את הנתונים החדשים
            else:
                st.sidebar.error("Analysis Failed. Check logs.")

# --- Main Content ---
st.title(f"Nutritional Report: {selected_user_label.split('(')[0]}")
st.caption("Real-time clinical analysis powered by GenAI & Optimization Algorithms")
st.divider()

# Get Data
df, meal_info = get_latest_meal_analysis(selected_user_id)

if df is not None and not df.empty:
    
    # --- Section A: Meal Analysis ---
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.subheader("📸 Last Meal")
        # אם יש תמונה שהועלתה הרגע - נציג אותה, אחרת נציג תמונת דמו
        # (במערכת אמיתית היינו שומרים את ה-URL של התמונה ב-S3, כאן נשתמש ב-Placeholder אם אין העלאה חיה)
        if uploaded_file:
             st.image(uploaded_file, use_container_width=True)
        else:
             st.image("test_meal.jpg", caption="Analyzed Image", use_container_width=True)

    with col2:
        st.subheader("🤖 Clinical Assessment")
        if not meal_info.empty:
            summary = meal_info.iloc[0]['ai_analysis_summary']
            st.info(summary)
        
        # Key Metrics Row
        def get_nutrient_val(name):
            row = df[df['nutrient_name'] == name]
            return row.iloc[0]['percentage'] if not row.empty else 0
            
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Iron Coverage", f"{get_nutrient_val('iron'):.0f}%")
        m2.metric("Calcium Coverage", f"{get_nutrient_val('calcium'):.0f}%")
        m3.metric("Vitamin B12", f"{get_nutrient_val('vitamin_b12'):.0f}%")
        m4.metric("Vitamin C", f"{get_nutrient_val('vitamin_c'):.0f}%")

    st.divider()

    # --- Section B: Graph ---
    st.subheader("📊 Micronutrient Status (vs. RDA)")
    
    # Color Logic: Red (<90%), Green (90-110%), Blue (>110%)
    df['color'] = df['percentage'].apply(lambda x: '#FF4B4B' if x < 90 else ('#00CC96' if x <= 110 else '#1C83E1'))
    df['display_name'] = df['nutrient_name'].str.replace('_',' ').str.title()
    
    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=df['display_name'], 
        y=df['percentage'], 
        marker_color=df['color'],
        text=df['percentage'].apply(lambda x: f"{x:.0f}%"),
        textposition='auto'
    ))
    
    # Add 100% Target Line
    fig.add_shape(type="line", x0=-0.5, x1=len(df)-0.5, y0=100, y1=100, 
                  line=dict(color="gray", width=2, dash="dash"))
    
    fig.update_layout(
        yaxis_title="% of Daily Value", 
        xaxis_tickangle=-45,
        height=450,
        margin=dict(t=20, b=20)
    )
    st.plotly_chart(fig, use_container_width=True)

    st.divider()

    # --- Section C: AI Recommendations ---
    st.subheader("💡 Smart Optimization Recommendations")
    st.write("The algorithm identifies deficiencies and suggests high-density foods to close the gap efficiently.")
    
    recommendations = recommend_food(selected_user_id)
    
    if recommendations:
        cols = st.columns(len(recommendations))
        for i, rec in enumerate(recommendations):
            with cols[i]:
                st.success(f"**{rec['food_name']}**")
                st.markdown(f"**Serving:** {rec['serving']}")
                st.markdown(f"**Cost:** Only {rec['calories']} kcal")
                st.markdown(f"**Why?** Covers: {rec['reason']}")
                # תגיות קטנות
                tags = rec['tags'].split(',')
                st.caption(" • ".join([t.strip() for t in tags[:2]]))
    else:
        st.balloons()
        st.success("Perfect! No significant deficiencies detected based on current intake.")

else:
    st.warning("No data found for this user. Please upload a meal image using the sidebar.")