import os
import requests
from fastapi import APIRouter, UploadFile, File, Form
from dotenv import load_dotenv
from groq import Groq
from services.pdf_processor import extract_text_from_pdf
import json

load_dotenv()

router = APIRouter()

client = Groq(api_key=os.getenv("GROQ_API_KEY"))
SARVAM_KEY = os.getenv("SARVAM_API_KEY")

UPLOAD_DIR = "temp_uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

LANG_MAP = {
    "en-IN": "English",
    "hi-IN": "Hindi",
    "kn-IN": "Kannada",
    "te-IN": "Telugu"
}

@router.post("/upload-pdf")
async def upload_pdf(
    file: UploadFile = File(...),
    target_lang: str = Form("en-IN")
):
    try:
        # Save PDF
        file_path = os.path.join(UPLOAD_DIR, file.filename)
        with open(file_path, "wb") as f:
            f.write(await file.read())

        # Extract text
        text = extract_text_from_pdf(file_path)

        if not text:
            return {"error": "No text found in PDF"}

        lang_name = LANG_MAP.get(target_lang, "English")

        # 🧠 LLM prompt
        prompt = f"""
You are a smart assistant.

1. Translate the text into {lang_name}
2. Summarize it clearly in {lang_name}
3. Create a chill conversational version

IMPORTANT:
- display_text → clean {lang_name}
- voice_text → casual, friendly, slightly mixed tone

Text:
{text[:3000]}

Return ONLY JSON:
{{
"display_text": "...",
"voice_text": "..."
}}
"""

        res = client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model="llama-3.3-70b-versatile",
            response_format={"type": "json_object"}
        )

        ai_output = json.loads(res.choices[0].message.content)

        display_text = ai_output.get("display_text", "")
        voice_text = ai_output.get("voice_text", "")

        # Split voice text
        chunk_size = 400
        chunks = [
            voice_text[i:i + chunk_size]
            for i in range(0, len(voice_text), chunk_size)
        ]

        # Generate audio
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