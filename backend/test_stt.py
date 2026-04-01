import requests
import os
from dotenv import load_dotenv

load_dotenv()

SARVAM_KEY = os.getenv("SARVAM_API_KEY")

def test_hearing(audio_file_path):
    print("👂 Testing Sarvam Shakti (STT)...")
    
    url = "https://api.sarvam.ai/speech-to-text"
    
    # Logic: Sending 'unknown' forces the AI to detect the language automatically
    payload = {
        'language_code': 'unknown', 
        'model': 'saaras:v3'
    }
    
    # In a real app, this will be the audio chunk from your frontend
    files = [
        ('file', ('audio.wav', open(audio_file_path, 'rb'), 'audio/wav'))
    ]
    
    headers = {
        "api-subscription-key": SARVAM_KEY
    }

    try:
        response = requests.post(url, headers=headers, data=payload, files=files)
        if response.status_code == 200:
            print("✅ SUCCESS! Speech recognized.")
            res_data = response.json()
            print(f"Transcript: {res_data.get('transcript')}")
            print(f"Detected Language: {res_data.get('language_code')}")
        else:
            print(f"❌ Error: {response.status_code}")
            print(response.text)
    except Exception as e:
        print(f"❌ Connection Error: {str(e)}")

if __name__ == "__main__":
    # Note: You'll need a small .wav file to run this successfully!
    print("Senior Dev Tip: If you don't have a .wav file, skip to the 'Bridge' step.")
    # test_hearing("test_audio.wav")