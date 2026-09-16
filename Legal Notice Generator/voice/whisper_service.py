# from faster_whisper import WhisperModel
# import tempfile
# import os

# # Load model only once
# model = WhisperModel(
#     "base",
#     device="cpu",
#     compute_type="int8"
# )

# def transcribe_audio(audio_file):

#     suffix = os.path.splitext(audio_file.filename)[1] or ".webm"

#     with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as temp:
#         audio_file.save(temp.name)
#         temp_path = temp.name

#     try:
#         segments, info = model.transcribe(
#             temp_path,
#             beam_size=5
#         )

#         text = " ".join(segment.text for segment in segments).strip()

#         return text

#     finally:
#         if os.path.exists(temp_path):
#             os.remove(temp_path)









from pathlib import Path
from groq import Groq
from config.config import GROQ_API_KEY

client = Groq(api_key=GROQ_API_KEY)

def transcribe_audio(audio_path):

    audio_path = Path(audio_path)

    with open(audio_path,"rb") as audio_file:

        transcription = client.audio.transcriptions.create(

            file=(audio_path.name,audio_file.read()),

            model="whisper-large-v3-turbo",

            response_format="json",

            temperature=0
        )

    return transcription.text