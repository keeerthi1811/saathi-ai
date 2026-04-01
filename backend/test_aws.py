import boto3
import json
import os
from dotenv import load_dotenv

load_dotenv()

client = boto3.client(
    service_name='bedrock-runtime',
    region_name=os.getenv("AWS_REGION"),
    aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
    aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY")
)

def verify_brain():
    print("🧠 Saathi is connecting via Global Inference Profile...")
    
    body = json.dumps({
        "anthropic_version": "bedrock-2023-05-31",
        "max_tokens": 500,
        "messages": [
            {
                "role": "user", 
                "content": "Bhai, confirm if you are online using the Global Inference Profile. Speak in Hinglish."
            }
        ]
    })

    try:
        response = client.invoke_model(
            # Using the Inference Profile ID instead of the Base Model ID
            modelId='global.anthropic.claude-sonnet-4-6', 
            body=body
        )
        
        result = json.loads(response.get('body').read())
        answer = result['content'][0]['text']
        
        print("\n✅ CONNECTION SUCCESSFUL!")
        print(f"Saathi says: {answer}")
        
    except Exception as e:
        print("\n❌ INFERENCE PROFILE ERROR")
        print(f"Error Details: {str(e)}")
        print("\nSenior Dev Tip: Go to Bedrock Console -> 'Inference Profiles' on the sidebar.")
        print("Ensure 'Cross-region inference' is enabled for your account.")

if __name__ == "__main__":
    verify_brain()