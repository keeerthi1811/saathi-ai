import os
import requests
from fastapi import APIRouter, UploadFile, File, Form
from dotenv import load_dotenv
from groq import Groq

load_dotenv()

router = APIRouter()

client = Groq(api_key=os.getenv("GROQ_API_KEY"))
SARVAM_KEY = os.getenv("SARVAM_API_KEY")


@router.post("/voice-quiz")
async def voice_quiz(
    audio: UploadFile = File(...),
    correct_answer: str = Form(...)
):
    try:
        audio_bytes = await audio.read()

        # 🔊 Speech to Text
        stt_res = requests.post(
            "https://api.sarvam.ai/speech-to-text",
            headers={"api-subscription-key": SARVAM_KEY},
            files={"file": ("audio.wav", audio_bytes, "audio/wav")},
            data={"language_code": "unknown"}
        ).json()

        user_answer = stt_res.get("transcript", "")

        # 🤖 Evaluate
        prompt = f"""
Correct answer: {correct_answer}
Student answer: {user_answer}

Check if correct and respond like a friendly teacher.
"""

        res = client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model="llama-3.3-70b-versatile"
        )

        feedback = res.choices[0].message.content

        # 🔊 Text to Speech
        tts_res = requests.post(
            "https://api.sarvam.ai/text-to-speech",
            headers={
                "api-subscription-key": SARVAM_KEY,
                "Content-Type": "application/json"
            },
            json={
                "inputs": [feedback],
                "target_language_code": "en-IN"
            }
        ).json()

        audio_out = tts_res.get("audios", [None])[0]

        return {
            "user_answer": user_answer,
            "feedback": feedback,
            "audio": audio_out
        }

    except Exception as e:
        return {"error": str(e)}