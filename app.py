import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import os
from db_handler import get_db_connection
from recommender_engine import recommend_food
from nutrition_ai import analyze_food_image

# --- Page Config ---
st.set_page_config(page_title="Clinical Nutrition AI", layout="wide", page_icon="🥗")

# --- 🎨 SUPERCHARGED CSS (עיצוב ברמת React) ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');

    /* גלובלי */
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
        background-color: #f3f4f6;
        color: #1f2937;
    }

    /* הסתרת אלמנטים מיותרים של סטרימליט */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}

    /* כותרות */
    h1 {
        color: #111827;
        font-weight: 800;
        letter-spacing: -1px;
        padding-top: 0;
    }
    h3 {
        color: #374151;
        font-weight: 600;
    }

    /* --- Sidebar --- */
    section[data-testid="stSidebar"] {
        background-color: #ffffff;
        border-right: 1px solid #e5e7eb;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
    }

    /* כפתורים */
    div.stButton > button {
        background: linear-gradient(135deg, #2563eb 0%, #1d4ed8 100%);
        color: white;
        border: none;
        padding: 12px 24px;
        border-radius: 8px;
        font-weight: 600;
        transition: all 0.2s;
        width: 100%;
        box-shadow: 0 4px 6px rgba(37, 99, 235, 0.2);
    }
    div.stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 10px rgba(37, 99, 235, 0.3);
        border: none;
        color: white;
    }

    /* --- Cards (Metrics) --- */
    div[data-testid="stMetric"] {
        background-color: #ffffff;
        border: 1px solid #e5e7eb;
        padding: 20px;
        border-radius: 12px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        transition: transform 0.2s;
    }
    div[data-testid="stMetric"]:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    div[data-testid="stMetric"] label {
        color: #6b7280 !important;
        font-size: 0.9rem !important;
        font-weight: 600;
    }
    div[data-testid="stMetric"] div[data-testid="stMetricValue"] {
        color: #1f2937 !important;
        font-size: 1.8rem !important;
        font-weight: 700;
    }

    /* --- Recommendation Cards (Custom HTML) --- */
    .rec-card {
        background: white;
        border: 1px solid #e5e7eb;
        border-radius: 12px;
        padding: 20px;
        margin-bottom: 20px;
        transition: all 0.3s ease;
        position: relative;
        overflow: hidden;
    }
    .rec-card:hover {
        transform: translateY(-4px);
        box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1);
        border-color: #2563eb;
    }
    .rec-title {
        color: #111827;
        font-weight: 700;
        font-size: 1.1rem;
        margin-bottom: 8px;
        display: flex;
        align-items: center;
        gap: 8px;
    }
    .rec-meta {
        font-size: 0.85rem;
        color: #6b7280;
        background: #f3f4f6;
        padding: 4px 8px;
        border-radius: 6px;
        display: inline-block;
        margin-bottom: 12px;
    }
    .rec-reason {
        background: #eff6ff;
        color: #1e40af;
        padding: 10px;
        border-radius: 8px;
        font-size: 0.9rem;
        margin-bottom: 10px;
    }
    .rec-tags span {
        background: #e5e7eb;
        color: #374151;
        padding: 2px 8px;
        border-radius: 12px;
        font-size: 0.75rem;
        font-weight: 600;
        margin-right: 5px;
    }

    /* --- General Layout --- */
    .block-container {
        padding-top: 2rem;
        padding-bottom: 5rem;
        max-width: 1200px;
    }
    .stAlert {
        border-radius: 10px;
    }
</style>
""", unsafe_allow_html=True)

# --- Data Functions (ללא שינוי) ---
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
    meal_info = pd.read_sql("SELECT ai_analysis_summary, created_at FROM meals WHERE user_id = %s ORDER BY created_at DESC LIMIT 1", conn, params=(user_id,))
    conn.close()
    return df, meal_info

# --- Sidebar ---
st.sidebar.image("https://cdn-icons-png.flaticon.com/512/3074/3074063.png", width=60)
st.sidebar.markdown("## Clinical AI Dietitian")

users = get_user_list()
user_map = {f"{row['full_name']} ({'Pregnant' if row['is_pregnant'] else row['gender']})": row['user_id'] for _, row in users.iterrows()}
selected_user_label = st.sidebar.selectbox("Select Patient Profile", list(user_map.keys()))
selected_user_id = user_map[selected_user_label]

st.sidebar.markdown("---")
st.sidebar.subheader("Analyze New Meal")
uploaded_file = st.sidebar.file_uploader("Upload Image", type=['jpg', 'jpeg', 'png'])

if uploaded_file is not None:
    st.sidebar.image(uploaded_file, caption="Preview", use_container_width=True)
    if st.sidebar.button("⚡ Run AI Analysis"):
        with st.spinner("Processing with AWS Bedrock..."):
            temp_filename = "temp_upload.jpg"
            with open(temp_filename, "wb") as f:
                f.write(uploaded_file.getbuffer())
            result = analyze_food_image(temp_filename, user_id=selected_user_id)
            if result:
                if os.path.exists(temp_filename): os.remove(temp_filename)
                st.rerun()

# --- Main Content ---
st.title(f"Nutritional Report")
st.markdown(f"**Patient:** {selected_user_label.split('(')[0]} | **Status:** Real-time Analysis")
st.markdown("---")

df, meal_info = get_latest_meal_analysis(selected_user_id)

if df is not None and not df.empty:
    
    # Section A: Summary & Metrics
    col1, col2 = st.columns([1, 2])
    
    with col1:
        # הצגת תמונה מעוצבת
        if uploaded_file:
             st.image(uploaded_file, use_container_width=True, caption="Analyzed Meal")
        else:
             st.image("test_meal.jpg", use_container_width=True, caption="Last Analyzed Meal")

    with col2:
        st.subheader("🤖 AI Clinical Assessment")
        if not meal_info.empty:
            st.info(meal_info.iloc[0]['ai_analysis_summary'])
        
        # Metrics - עם צבעים דינמיים
        def get_val(name):
            row = df[df['nutrient_name'] == name]
            return row.iloc[0]['percentage'] if not row.empty else 0
        
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Iron", f"{get_val('iron'):.0f}%")
        m2.metric("Calcium", f"{get_val('calcium'):.0f}%")
        m3.metric("B12", f"{get_val('vitamin_b12'):.0f}%")
        m4.metric("Vit C", f"{get_val('vitamin_c'):.0f}%")

    st.markdown("---")

    # Section B: Chart
    st.subheader("📊 Micronutrient Status (vs. RDA)")
    
    df['color'] = df['percentage'].apply(lambda x: '#ef4444' if x < 90 else ('#10b981' if x <= 110 else '#3b82f6'))
    df['display_name'] = df['nutrient_name'].str.replace('_',' ').str.title()
    
    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=df['display_name'], 
        y=df['percentage'], 
        marker_color=df['color'],
        text=df['percentage'].apply(lambda x: f"{x:.0f}%"),
        textposition='auto',
        marker_cornerradius=5
    ))
    
    fig.update_layout(
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        yaxis_title="% of Daily Value",
        xaxis_tickangle=-45,
        height=400,
        margin=dict(t=20, b=20)
    )
    st.plotly_chart(fig, use_container_width=True)

    st.markdown("---")

    # Section C: Recommendations (Custom HTML Cards!)
    st.subheader("💡 Smart Optimization Recommendations")
    
    recommendations = recommend_food(selected_user_id)
    
    if recommendations:
        # שימוש בעמודות של סטרימליט כדי להחזיק את ה-HTML
        cols = st.columns(len(recommendations))
        
        for i, rec in enumerate(recommendations):
            with cols[i]:
                # יצירת HTML מותאם אישית לכרטיסייה
                html_card = f"""
                <div class="rec-card">
                    <div class="rec-title">🍽️ {rec['food_name']}</div>
                    <div class="rec-meta">
                        📏 {rec['serving']} | 🔥 {rec['calories']} kcal
                    </div>
                    <div class="rec-reason">
                        <strong>Why?</strong> {rec['reason']}
                    </div>
                    <div class="rec-tags">
                        {''.join([f'<span>{t.strip()}</span>' for t in rec['tags'].split(',')[:2]])}
                    </div>
                </div>
                """
                st.markdown(html_card, unsafe_allow_html=True)
    else:
        st.balloons()
        st.success("Target Achieved! No recommendations needed.")

else:
    st.warning("No data found. Upload a meal to begin.")