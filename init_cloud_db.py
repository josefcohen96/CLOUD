import psycopg2
import os

# פרטי ההתחברות ל-RDS שלך (העתקתי ממה ששלחת קודם)
DB_HOST = "database-1.cmtkkqyiagdy.us-east-1.rds.amazonaws.com"
DB_NAME = "postgres"
DB_USER = "postgres"
DB_PASS = "Karina1256"

# הטבלאות שצריך ליצור
CREATE_USERS_TABLE = """
CREATE TABLE IF NOT EXISTS users (
    user_id SERIAL PRIMARY KEY,
    full_name VARCHAR(100),
    date_of_birth DATE,
    gender VARCHAR(10),
    is_pregnant BOOLEAN DEFAULT FALSE,
    is_lactating BOOLEAN DEFAULT FALSE
);
"""

CREATE_MEALS_TABLE = """
CREATE TABLE IF NOT EXISTS meals (
    meal_id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(user_id),
    image_url TEXT,
    ai_analysis_summary TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
"""

CREATE_FOOD_ITEMS_TABLE = """
CREATE TABLE IF NOT EXISTS food_items (
    item_id SERIAL PRIMARY KEY,
    meal_id INTEGER REFERENCES meals(meal_id),
    food_name VARCHAR(100),
    estimated_weight_g FLOAT,
    calories_kcal FLOAT,
    protein_g FLOAT,
    carbs_g FLOAT,
    fat_g FLOAT
);
"""

CREATE_MICROS_TABLE = """
CREATE TABLE IF NOT EXISTS consumed_micros (
    micro_id SERIAL PRIMARY KEY,
    item_id INTEGER REFERENCES food_items(item_id),
    nutrient_name VARCHAR(50),
    amount FLOAT,
    unit VARCHAR(10)
);
"""

# הנתונים שאנחנו רוצים להכניס
INITIAL_USERS = [
    # שם, תאריך לידה, מגדר, הריון, הנקה
    ('Yossi Cohen', '1996-05-20', 'male', False, False),
    ('Danny Sporty', '1998-01-01', 'male', False, False),
    ('Dana Pregnant', '1995-03-15', 'female', True, False)
]

def init_db():
    try:
        print(f"🔌 Connecting to AWS RDS: {DB_HOST}...")
        conn = psycopg2.connect(
            host=DB_HOST,
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASS
        )
        cur = conn.cursor()

        print("🔨 Creating tables if not exist...")
        cur.execute(CREATE_USERS_TABLE)
        cur.execute(CREATE_MEALS_TABLE)
        cur.execute(CREATE_FOOD_ITEMS_TABLE)
        cur.execute(CREATE_MICROS_TABLE)
        
        print("🌱 Seeding initial users...")
        for user in INITIAL_USERS:
            # בודק אם המשתמש כבר קיים לפי שם כדי לא ליצור כפילויות
            cur.execute("SELECT user_id FROM users WHERE full_name = %s", (user[0],))
            if cur.fetchone() is None:
                cur.execute("""
                    INSERT INTO users (full_name, date_of_birth, gender, is_pregnant, is_lactating)
                    VALUES (%s, %s, %s, %s, %s)
                """, user)
                print(f"   > Added user: {user[0]}")
            else:
                print(f"   > User {user[0]} already exists.")

        conn.commit()
        cur.close()
        conn.close()
        print("✅ Database initialized successfully!")

    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    init_db()