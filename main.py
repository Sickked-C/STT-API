from fastapi import FastAPI, UploadFile, File, HTTPException
from groq import Groq
from decouple import config
import shutil
import os
app = FastAPI(title="Speech-to-Text API")
GROQ_API_KEY = config("GROQ_API_KEY")
TEMP_DIR = config("TEMP_DIR", default="temp_audio")
os.makedirs(TEMP_DIR, exist_ok=True)
SUPPORTED_LANGUAGES = {
    'vi': 'vi',
    'en': 'en',
    'auto': 'auto'
}
_client = None
def get_client():
    global _client
    if _client is None:
        _client = Groq(api_key=GROQ_API_KEY)
    return _client

def transcribe_with_groq(file_path: str, language: str) -> str:
    client = get_client()
    with open(file_path, 'rb') as audio_file:
        transcription = client.audio.transcriptions.create(
            model = "whisper-large-v3",
            file=audio_file,
            language=None if language == "auto" else language,
            response_format="text"
        )
    return transcription

@app.get("/")
def root():
    return {
        "message": "STT API is running",
        "model" : "Whisper-large-v3 via Groq",
        "docs": "/docs"
        }

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/transcribe")
async def transcribe(file: UploadFile = File(...), language: str = "auto"):
    if language not in SUPPORTED_LANGUAGES:
        raise HTTPException(status_code=400, detail="Language must be 'vi', 'en'")
    if not file.filename.endswith(('.wav', '.mp3', '.m4a', '.ogg')):
        raise HTTPException(status_code=400, detail="Supported formats: .wav, .mp3, .m4a, .ogg")
    
    temp_path = os.path.join(TEMP_DIR, file.filename)
    with open(temp_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    try:
        result = transcribe_with_groq(temp_path, language)
        return{
            "filename": file.filename,
            "language": language,
            "transcription": result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)