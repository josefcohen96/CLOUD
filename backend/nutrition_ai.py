import boto3
import json
import base64
import os
from botocore.exceptions import ClientError
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

# --- עדכון: הוספת image_url כפרמטר ---
def analyze_food_image(image_path, user_id=1, image_url=None):
    client = get_bedrock_client()
    if not client:
        return None

    if not os.path.exists(image_path):
        print(f"Error: Image not found at {image_path}")
        return None
    
    base64_image = encode_image_to_base64(image_path)

    system_prompt = """
    You are an advanced clinical dietitian AI. 
    Your goal is to provide a highly detailed nutritional analysis of food images.
    """

    user_message = """
    Analyze this meal image with high precision.
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
        print(f"Sending image to AWS Bedrock...")
        response = client.invoke_model(modelId=MODEL_ID, body=json.dumps(payload))
        result_body = json.loads(response['body'].read())
        response_text = result_body['content'][0]['text']
        
        # --- תיקון: שליחת ה-URL האמיתי מה-S3 במקום טקסט קבוע ---
        print(f"\n💾 Saving to Database for User {user_id} with URL: {image_url}")
        save_meal_to_db(user_id=user_id, image_url=image_url, ai_json_text=response_text)
        
        return response_text

    except ClientError as e:
        print(f"Error calling Bedrock: {e}")
        return None