import boto3
import botocore

def check_environment():
    print(f"✅ Boto3 Version: {boto3.__version__}")
    print(f"✅ Botocore Version: {botocore.__version__}")
    
    # בדיקה פשוטה שאנחנו מעל הגרסה הקריטית
    major, minor, patch = map(int, boto3.__version__.split('.'))
    if minor < 36: # גרסאות לפני 1.36 לא מכירות את סונט 3.5 כמו שצריך
        print("❌ WARNING: Your boto3 version is too old for the latest Claude models!")
        print("   Please run: pip install --upgrade boto3")
    else:
        print("✅ Version check passed. You are ready for Claude 3.5/4.5.")

    # נסיון למצוא את המודל החדש ברשימה של AWS
    try:
        bedrock = boto3.client('bedrock', region_name='us-east-1')
        print("\nChecking access to new models in us-east-1...")
        
        # נבקש את רשימת המודלים של Anthropic
        response = bedrock.list_foundation_models(byProvider='anthropic')
        
        found_models = []
        for model in response.get('modelSummaries', []):
            model_id = model['modelId']
            # נחפש ספציפית את החדשים
            if 'sonnet' in model_id:
                found_models.append(model_id)
        
        if found_models:
            print(f"✅ Found {len(found_models)} Sonnet models available to you:")
            for m in found_models:
                print(f"   - {m}")
        else:
            print("⚠️ No Sonnet models found. Check your Region or Model Access settings.")
            
    except Exception as e:
        print(f"❌ Error connecting to Bedrock: {e}")

if __name__ == "__main__":
    check_environment()