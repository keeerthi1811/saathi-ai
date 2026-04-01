import boto3
import os
from dotenv import load_dotenv

load_dotenv()

client = boto3.client(
    service_name='bedrock', # Note: 'bedrock', not 'bedrock-runtime'
    region_name='us-east-1', # Check the mothership region
    aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
    aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY")
)

def list_my_models():
    print("🔍 Searching for your available Claude models...")
    try:
        # This lists all models AND inference profiles
        profiles = client.list_inference_profiles()
        for p in profiles['inferenceProfileSummaries']:
            if 'claude' in p['inferenceProfileId']:
                print(f"✅ Found ID: {p['inferenceProfileId']}")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    list_my_models()