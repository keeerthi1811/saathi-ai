import os
import json
from fastapi import APIRouter, UploadFile, File
from dotenv import load_dotenv
from groq import Groq
from services.pdf_processor import extract_text_from_pdf

load_dotenv()

router = APIRouter()

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

UPLOAD_DIR = "temp_uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)


@router.post("/study-upload")
async def study_upload(file: UploadFile = File(...)):
    try:
        # Save file
        file_path = os.path.join(UPLOAD_DIR, file.filename)
        with open(file_path, "wb") as f:
            f.write(await file.read())

        # Extract text
        text = extract_text_from_pdf(file_path)

        if not text:
            return {"error": "No text found"}

        # AI generate study material
        prompt = f"""
You are an AI tutor.

From this content generate:
1. Short summary
2. 5 quiz questions with answers

Return JSON:
{{
  "summary": "...",
  "quiz": [
    {{
      "question": "...",
      "answer": "..."
    }}
  ]
}}

Text:
{text[:3000]}
"""

        res = client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model="llama-3.3-70b-versatile",
            response_format={"type": "json_object"}
        )

        output = json.loads(res.choices[0].message.content)

        return output

    except Exception as e:
        return {"error": str(e)}