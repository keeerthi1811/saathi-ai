import requests
import os
import json
from dotenv import load_dotenv

load_dotenv()

SARVAM_KEY = os.getenv("SARVAM_API_KEY")

def test_sarvam_voice():
    print("🗣️ Testing Sarvam Bulbul (TTS)...")
    
    url = "https://api.sarvam.ai/text-to-speech"
    
    payload = {
        "inputs": ["Haan bhai, Bedrock toh chal gaya, ab meri awaaz check karo!"],
        "target_language_code": "hi-IN",
        "speaker": "shubh", # This is the best 'Bhai' vibe voice
        "model": "bulbul:v3"
    }
    
    headers = {
        "api-subscription-key": SARVAM_KEY,
        "Content-Type": "application/json"
    }

    try:
        response = requests.post(url, json=payload, headers=headers)
        if response.status_code == 200:
            res_data = response.json()
            # The API returns a list of base64 audio strings
            if res_data.get("audios"):
                print("✅ SUCCESS! Sarvam generated the audio.")
                print(f"Audio Data received (first 50 chars): {res_data['audios'][0][:50]}...")
            else:
                print("⚠️ Sarvam returned success but no audio data.")
        else:
            print(f"❌ Sarvam Error: {response.status_code}")
            print(response.text)
            
    except Exception as e:
        print(f"❌ Connection Error: {str(e)}")

if __name__ == "__main__":
    test_sarvam_voice()