from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from mangum import Mangum
from routers import users, meals, recommendations

app = FastAPI(root_path="/default")

# אפשור גישה מה-Frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(users.router)
app.include_router(meals.router)
app.include_router(recommendations.router)

handler = Mangum(app)