from fastapi import APIRouter
from recommender_engine import recommend_food

router = APIRouter()

@router.get("/recommendations/{user_id}")
def get_recommendations_endpoint(user_id: int):
    return recommend_food(user_id)
