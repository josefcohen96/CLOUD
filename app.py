import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from db_handler import get_db_connection
from recommender_engine import recommend_food

# --- הגדרת עמוד ---
st.set_page_config(page_title="Smart Nutrition AI", layout="wide", page_icon="🥗")

# CSS לעיצוב כרטיסים
st.markdown("""
<style>
    .stMetric {
        background-color: #f0f2f6;
        padding: 10px;
        border-radius: 10px;
    }
    div[data-testid="stExpander"] {
        border: 1px solid #e0e0e0;
        border-radius: 10px;
    }
</style>
""", unsafe_allow_html=True)

# --- פונקציות ---
def get_user_list():
    conn = get_db_connection()
    df = pd.read_sql("SELECT user_id, full_name FROM users ORDER BY user_id", conn)
    conn.close()
    return df

def get_latest_meal_analysis(user_id):
    conn = get_db_connection()
    
    # 1. פרופיל
    user_query = "SELECT gender, (CURRENT_DATE - date_of_birth)/30, CASE WHEN is_pregnant THEN 'pregnancy' ELSE 'normal' END FROM users WHERE user_id = %s"
    cur = conn.cursor()
    cur.execute(user_query, (user_id,))
    prof = cur.fetchone()
    if not prof: return None, None
    gender, age_months, condition = prof
    
    # 2. נתונים
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
    meal_info = pd.read_sql("SELECT ai_analysis_summary, created_at FROM meals WHERE user_id = %s ORDER BY created_at DESC LIMIT 1", conn, params=(user_id,))
    conn.close()
    return df, meal_info

# --- UI ---
st.sidebar.title("🥑 Smart Dietitian AI")
users = get_user_list()
user_map = {row['full_name']: row['user_id'] for _, row in users.iterrows()}
selected_user = st.sidebar.selectbox("בחר מטופל:", list(user_map.keys()))
uid = user_map[selected_user]

st.title(f"דוח קליני: {selected_user}")
st.divider()

df, meal_info = get_latest_meal_analysis(uid)

if df is not None and not df.empty:
    # 1. Meal Summary
    c1, c2 = st.columns([1, 2])
    with c1:
        st.image("test_meal.jpg", use_container_width=True, caption="הארוחה האחרונה")
    with c2:
        st.info(f"📝 **AI Analysis:** {meal_info.iloc[0]['ai_analysis_summary']}")
        
        # KPI Bar
        k1, k2, k3, k4 = st.columns(4)
        
        # פונקציות עזר לשליפת נתונים בטוחה
        def get_val(name):
            row = df[df['nutrient_name'] == name]
            if not row.empty:
                return row.iloc[0]['percentage']
            return 0
            
        k1.metric("Iron (ברזל)", f"{get_val('iron'):.0f}%")
        k2.metric("Vitamin B12", f"{get_val('vitamin_b12'):.0f}%")
        k3.metric("Vitamin C", f"{get_val('vitamin_c'):.0f}%")
        k4.metric("Zinc (אבץ)", f"{get_val('zinc'):.0f}%")

    st.divider()

    # 2. Status Chart
    st.subheader("📊 סטטוס תזונתי (RDA Coverage)")
    df['color'] = df['percentage'].apply(lambda x: '#FF4B4B' if x < 90 else ('#00CC96' if x <= 110 else '#1C83E1'))
    df['display'] = df['nutrient_name'].str.replace('_',' ').str.title()
    
    fig = go.Figure()
    fig.add_trace(go.Bar(x=df['display'], y=df['percentage'], marker_color=df['color'], text=df['percentage'].apply(lambda x: f"{x:.0f}%"), textposition='auto'))
    fig.add_shape(type="line", x0=-0.5, x1=len(df)-0.5, y0=100, y1=100, line=dict(color="gray", dash="dash"))
    st.plotly_chart(fig, use_container_width=True)
    
    st.divider()

    # 3. AI Recommendations
    st.subheader("💡 AI Smart Recommendations (Greedy Algorithm)")
    st.caption("המלצות אופטימליות להשלמת חוסרים במינימום קלוריות:")
    
    recs = recommend_food(uid)
    
    if recs:
        cols = st.columns(len(recs))
        for i, r in enumerate(recs):
            with cols[i]:
                st.success(f"**{r['food_name']}**")
                st.markdown(f"**מנה:** {r['serving']}")
                st.markdown(f"**קלוריות:** {r['calories']}")
                st.markdown(f"**למה זה נבחר?**")
                st.caption(f"מכסה: {r['reason']}")
    else:
        st.balloons()
        st.success("התזונה שלך מושלמת היום! אין המלצות.")

else:
    st.warning("אין נתונים. הרץ את nutrition_ai.py כדי לטעון ארוחה.")