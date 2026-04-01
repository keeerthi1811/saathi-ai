import os
import requests
import json
from fastapi import APIRouter, UploadFile, File, Form
from dotenv import load_dotenv
from groq import Groq
from services.video_processor import save_video, extract_audio

load_dotenv()

router = APIRouter()

client = Groq(api_key=os.getenv("GROQ_API_KEY"))
SARVAM_KEY = os.getenv("SARVAM_API_KEY")

LANG_MAP = {
    "en-IN": "English",
    "hi-IN": "Hindi",
    "kn-IN": "Kannada",
    "te-IN": "Telugu"
}


@router.post("/upload-video")
async def upload_video(
    file: UploadFile = File(...),
    target_lang: str = Form("en-IN")
):
    try:
        # 1. Save video
        video_path = await save_video(file)

        # 2. Extract audio
        audio_path = extract_audio(video_path)

        # 3. Read audio
        with open(audio_path, "rb") as f:
            audio_bytes = f.read()

        # 4. STT
        stt_res = requests.post(
            "https://api.sarvam.ai/speech-to-text",
            headers={"api-subscription-key": SARVAM_KEY},
            files={"file": ("audio.wav", audio_bytes, "audio/wav")},
            data={"language_code": "unknown", "model": "saaras:v3"}
        ).json()

        transcript = stt_res.get("transcript", "")

        if not transcript:
            return {"error": "No speech detected"}

        lang_name = LANG_MAP.get(target_lang, "English")

        # 🧠 AI processing
        prompt = f"""
You are a smart assistant.

1. Translate into {lang_name}
2. Summarize clearly
3. Create chill conversational explanation

Return JSON:
{{
"display_text": "...",
"voice_text": "..."
}}

Text:
{transcript[:3000]}
"""

        res = client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model="llama-3.3-70b-versatile",
            response_format={"type": "json_object"}
        )

        ai_output = json.loads(res.choices[0].message.content)

        display_text = ai_output.get("display_text", "")
        voice_text = ai_output.get("voice_text", "")

        # 🔊 Chunk audio
        chunk_size = 400
        chunks = [
            voice_text[i:i + chunk_size]
            for i in range(0, len(voice_text), chunk_size)
        ]

        audio_chunks = []

        for chunk in chunks:
            tts_res = requests.post(
                "https://api.sarvam.ai/text-to-speech",
                headers={
                    "api-subscription-key": SARVAM_KEY,
                    "Content-Type": "application/json"
                },
                json={
                    "inputs": [chunk],
                    "target_language_code": target_lang,
                    "speaker": "shubh",
                    "model": "bulbul:v3"
                }
            ).json()

            if "audios" in tts_res and len(tts_res["audios"]) > 0:
                audio_chunks.append(tts_res["audios"][0])

        return {
            "text": display_text,
            "audio_chunks": audio_chunks
        }

    except Exception as e:
        return {"error": str(e)}