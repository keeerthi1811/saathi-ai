import os
import subprocess
from fastapi import UploadFile
import uuid

UPLOAD_DIR = "temp_uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)


async def save_video(file: UploadFile):
    file_path = os.path.join(UPLOAD_DIR, file.filename)
    with open(file_path, "wb") as f:
        f.write(await file.read())
    return file_path


def extract_audio(video_path: str):
   

    unique_id = str(uuid.uuid4())
    audio_path = f"temp_uploads/audio_{unique_id}.wav"

    command = [
        "ffmpeg",   # ✅ USE THIS ONLY
        "-i", video_path,
        "-vn",
        "-acodec", "pcm_s16le",
        "-ar", "16000",
        "-ac", "1",
        audio_path
    ]

    try:
        print("Running FFmpeg command:", command)  # 🔍 debug
        subprocess.run(command, check=True)
    except Exception as e:
        print("❌ FFmpeg error:", e)
        raise

    return audio_path