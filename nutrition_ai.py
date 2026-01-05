import boto3
import json
import base64
import os
from botocore.exceptions import ClientError
# --- שים לב: אנחנו חייבים לייבא את הפונקציה ששומרת ל-DB ---
from db_handler import save_meal_to_db 

MODEL_ID = "us.anthropic.claude-sonnet-4-5-20250929-v1:0" 
REGION = "us-east-1" 

def get_bedrock_client():
    try:
        return boto3.client(service_name='bedrock-runtime', region_name=REGION)
    except ClientError as e:
        print(f"Error connecting to AWS: {e}")
        return None

def encode_image_to_base64(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')

def analyze_food_image(image_path):
    client = get_bedrock_client()
    if not client:
        return

    if not os.path.exists(image_path):
        print(f"Error: Image not found at {image_path}")
        return
    
    base64_image = encode_image_to_base64(image_path)

    # הפרומפט המעודכן שלך (מצוין!)
    system_prompt = """
    You are an advanced clinical dietitian AI. 
    Your goal is to provide a highly detailed nutritional analysis of food images.
    You must estimate not just macros, but a comprehensive profile of micronutrients (vitamins and minerals).
    If a food source is known to contain specific nutrients (e.g., meat has B12 and Zinc), you must estimate them.
    """

    user_message = """
    Analyze this meal image with high precision.
    1. Identify all food items.
    2. Estimate weight in grams (be realistic).
    3. Output the nutritional data in JSON format.
    
    For each item, you MUST estimate:
    - Macros: Calories, Protein, Carbs, Fat.
    - Micros: Vitamin A, C, D, E, K, B-Vitamins (B1, B2, B3, B6, B12, Folate), 
      Calcium, Iron, Magnesium, Phosphorus, Potassium, Sodium, Zinc.

    Output structure (JSON only):
    {
        "overall_analysis": "Summary...",
        "items": [
            {
                "food_name": "Item Name",
                "estimated_weight_grams": 100,
                "macros": { ... },
                "micros": { "Iron": "2mg", ... }
            }
        ]
    }
    """
    
    payload = {
        "anthropic_version": "bedrock-2023-05-31",
        "max_tokens": 4096,
        "temperature": 0.1,
        "system": [{"type": "text", "text": system_prompt}],
        "messages": [
            {
                "role": "user",
                "content": [
                    {"type": "image", "source": {"type": "base64", "media_type": "image/jpeg", "data": base64_image}},
                    {"type": "text", "text": user_message}
                ]
            }
        ]
    }

    try:
        print(f"Sending image to AWS Bedrock ({MODEL_ID})...")
        response = client.invoke_model(modelId=MODEL_ID, body=json.dumps(payload))

        result_body = json.loads(response['body'].read())
        response_text = result_body['content'][0]['text']
        
        print("\n--- Analysis Result ---")
        print(response_text)

        # === התיקון הקריטי: שמירה לדאטה בייס ===
        # כאן אנחנו בוחרים לאיזה משתמש לשמור את המידע (1=יוסי, 2=ספורטאי, 3=הריון)
        # כרגע נשמור ליוסי (1)
        print("\n💾 Saving to Database...")
        save_meal_to_db(user_id=1, image_url="local_test.jpg", ai_json_text=response_text)
        
        return response_text

    except ClientError as e:
        print(f"Error calling Bedrock: {e}")

if __name__ == "__main__":
    image_file = "test_meal.jpg" 
    if not os.path.exists(image_file):
        print(f"Please place a food image named '{image_file}' in this folder.")
    else:
        analyze_food_image(image_file)