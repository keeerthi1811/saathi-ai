import os
import json
import base64
import requests
import wikipedia
from datetime import datetime
from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from groq import Groq
from routes.video import router as video_router
from routes.pdf import router as pdf_router
from routes.study import router as study_router
from routes.voice_quiz import router as voice_quiz_router



# 🔐 Load ENV
load_dotenv()

app = FastAPI()
app.include_router(video_router)
app.include_router(pdf_router)
app.include_router(study_router)
app.include_router(voice_quiz_router)


# 🌐 CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# 🔑 Keys
client = Groq(api_key=os.getenv("GROQ_API_KEY"))
SARVAM_KEY = os.getenv("SARVAM_API_KEY")

# 📚 Wiki helper
def get_wiki_info(query):
    try:
        wikipedia.set_lang("en")
        return wikipedia.summary(query, sentences=2)
    except:
        return None


@app.websocket("/ws/chat")
async def saathi_conversation(websocket: WebSocket):
    await websocket.accept()
    print("🤝 Saathi is online!")

    try:
        while True:
            data = await websocket.receive_json()

            audio_b64 = data.get("audio")
            ui_lang = data.get("ui_lang", "English")  # still used for display text

            if not audio_b64:
                continue

            # ==============================
            # 🎤 A. HEAR (STT)
            # ==============================
            try:
                audio_bytes = base64.b64decode(audio_b64)

                stt_res = requests.post(
                    "https://api.sarvam.ai/speech-to-text",
                    headers={"api-subscription-key": SARVAM_KEY},
                    files={"file": ("input.wav", audio_bytes, "audio/wav")},
                    data={"language_code": "unknown", "model": "saaras:v3"}
                ).json()

                transcript = stt_res.get("transcript", "")
                detected_lang = stt_res.get("language_code", "en-IN")

            except Exception as e:
                print("❌ STT Error:", e)
                continue

            if not transcript:
                continue

            # 🔍 LOGGING
            print("\n==============================")
            print("🗣 USER SAID:", transcript)
            print("🌐 DETECTED LANGUAGE:", detected_lang)

            # ==============================
            # 🧠 B. THINK
            # ==============================
            current_time = datetime.now().strftime("%I:%M %p")

            wiki_info = ""
            action = None
            yt_url = None

            # 🎯 AI INTENT DETECTION
            try:
                intent_prompt = f"""
                User said: "{transcript}"

                Classify the intent:
                - "play_youtube" → if user wants to play song/music/video
                - "wiki" → if asking about something
                - "normal" → anything else

                Return ONLY one word.
                """

                intent_res = client.chat.completions.create(
                    messages=[{"role": "user", "content": intent_prompt}],
                    model="llama-3.3-70b-versatile"
                )

                intent = intent_res.choices[0].message.content.strip().lower()

            except Exception as e:
                print("❌ Intent Error:", e)
                intent = "normal"

            # 🎯 Handle intents
            if "play_youtube" in intent:
                action = "play_youtube"
                yt_url = f"https://www.youtube.com/results?search_query={transcript}"

            elif "wiki" in intent:
                wiki_info = get_wiki_info(transcript)

            # ==============================
            # 🤖 SYSTEM PROMPT
            # ==============================
            system_prompt = (
                f"You are Saathi, a cool, street-smart AI friend. Time: {current_time}. "
                "Use casual tone .\n"

                f"User language code: {detected_lang}.\n"

                "RESPONSE RULES:\n"
                "- hi-IN → Hinglish\n"
                "- kn-IN → Kanglish\n"
                "- te-IN → Telugu-English mix\n"
                "- en-IN → Casual English\n"

                f"Also translate the response cleanly into {ui_lang}.\n"

                "RETURN ONLY JSON:\n"
                "{\"voice_text\": \"...\", \"display_text\": \"...\"}"
            )

            user_input = transcript
            if wiki_info:
                user_input = f"Fact: {wiki_info}. Explain simply: {transcript}"

            # ==============================
            # 🤖 AI RESPONSE
            # ==============================
            try:
                chat_completion = client.chat.completions.create(
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_input},
                    ],
                    model="llama-3.3-70b-versatile",
                    response_format={"type": "json_object"}
                )

                ai_raw = chat_completion.choices[0].message.content

                try:
                    ai_response = json.loads(ai_raw)
                except:
                    print("⚠️ JSON Parse Failed:", ai_raw)
                    ai_response = {
                        "voice_text": "Bhai system thoda confuse ho gaya 😅",
                        "display_text": "Something went wrong"
                    }

                voice_reply = ai_response.get("voice_text", "")
                display_reply = ai_response.get("display_text", "")

            except Exception as e:
                print("❌ AI Error:", e)
                continue

            # 🔍 LOGGING (AI)
            print("🤖 AI VOICE RESPONSE:", voice_reply)
            print("📺 DISPLAY RESPONSE:", display_reply)

            # ==============================
            # 🔊 C. SPEAK (TTS)
            # ==============================
            audio_output = None

            try:
                tts_res = requests.post(
                    "https://api.sarvam.ai/text-to-speech",
                    headers={
                        "api-subscription-key": SARVAM_KEY,
                        "Content-Type": "application/json"
                    },
                    json={
                        "inputs": [voice_reply],
                        "target_language_code": detected_lang,
                        "speaker": "shubh",
                        "model": "bulbul:v3"
                    }
                ).json()

                if "audios" in tts_res and len(tts_res["audios"]) > 0:
                    audio_output = tts_res["audios"][0]

            except Exception as e:
                print("❌ TTS Error:", e)

            print("==============================\n")

            # ==============================
            # 📤 SEND
            # ==============================
            await websocket.send_json({
                "user_text": transcript,
                "bot_voice_text": voice_reply,
                "bot_display_text": display_reply,
                "language": detected_lang,
                "audio": audio_output,
                "action": action,
                "youtube_url": yt_url
            })

    except Exception as e:
        print(f"🔌 WebSocket Error: {e}")