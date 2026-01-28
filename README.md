# 🥗 Nutrition AI Cloud Project

ברוכים הבאים לפרויקט ניהול התזונה החכם בענן! אפליקציה זו משלבת ממשק משתמש מודרני עם בינה מלאכותית למתן המלצות תזונה מותאמות אישית.

## 🚀 תכונות מרכזיות

*   **מעקב ארוחות**: רישום פשוט ומהיר של ארוחות וקלוריות.
*   **היסטוריה וניתוח נתונים**: צפייה בהיסטוריית ארוחות עם גרפים ויזואליים (באמצעות Recharts).
*   **מנוע המלצות AI**: מערכת חכמה הממליצה על ארוחות בהתבסס על העדפות והיסטוריה (Python & Pandas).
*   **ניהול משתמשים**: מערכת הרשמה והתחברות.

## 🛠️ טכנולוגיות

הפרויקט בנוי בארכיטקטורת Microservices מודרנית:

### Frontend (צד לקוח)
*   **Framework**: React 19
*   **Build Tool**: Vite
*   **UI/Icons**: Lucide React
*   **Charts**: Recharts
*   **HTTP Client**: Axios

### Backend (צד שרת)
*   **Framework**: FastAPI (Python)
*   **Server**: Uvicorn
*   **Database Integration**: PostgreSQL (Psycopg2)
*   **Caching**: Redis
*   **Cloud Integration**: AWS (Boto3, Mangum for Lambda support)

### Infrastructure
*   **Containerization**: Docker & Docker Compose

## 📦 התקנה והרצה

### אפשרות 1: הרצה באמצעות Docker (מומלץ)

וודא ש-Docker מותקן ורץ במחשב שלך.

1.  שכפל את המאגר:
    ```bash
    git clone <repository-url>
    cd nutrition
    ```

2.  הרץ את השירותים:
    ```bash
    docker-compose up --build -d
    ```

3.  פתח את הדפדפן:
    *   **Frontend**: http://localhost:5173
    *   **Backend API**: http://localhost:8000/docs (Swagger UI)

### אפשרות 2: הרצה ידנית

#### Backend
```bash
cd backend
pip install -r req.txt
uvicorn main:app --reload
```

#### Frontend
```bash
cd frontend
npm install
npm run dev
```

## 📂 מבנה הפרויקט

```
nutrition/
├── backend/            # קוד השרת (FastAPI)
│   ├── routers/        # נתיבי API (Users, Meals, Recommendations)
│   ├── main.py         # נקודת הכניסה לאפליקציה
│   └── ...
├── frontend/           # קוד הלקוח (React)
│   ├── src/
│   │   ├── components/
│   │   └── ...
└── docker-compose.yml  # הגדרות הרצה בקונטיינרים
```
