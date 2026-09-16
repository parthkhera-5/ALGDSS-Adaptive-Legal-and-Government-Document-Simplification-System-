# from flask import Blueprint, request, jsonify
# from voice.whisper_service import transcribe_audio

# voice_bp = Blueprint("voice", __name__)

# @voice_bp.route("/api/voice", methods=["POST"])
# def voice():

#     if "audio" not in request.files:
#         return jsonify(
#             success=False,
#             error="Audio file is required."
#         ),400

#     audio = request.files["audio"]

#     transcript = transcribe_audio(audio)

#     return jsonify(
#         success=True,
#         transcript=transcript
#     )











from pathlib import Path
from flask import Blueprint, request, jsonify
from werkzeug.utils import secure_filename

from voice.whisper_service import transcribe_audio
from config.config import ORIGINAL_DIR

voice_bp = Blueprint("voice", __name__)

@voice_bp.route("/api/voice", methods=["POST"])
def voice_api():

    save_path = None

    try:

        if "audio" not in request.files:
            return jsonify(success=False, error="Audio file missing"), 400

        audio = request.files["audio"]

        filename = secure_filename(audio.filename)

        save_path = ORIGINAL_DIR / filename

        audio.save(str(save_path))

        # Speech-to-Text using Groq Whisper
        transcript = transcribe_audio(save_path)

        # Delete temporary audio file
        if save_path.exists():
            save_path.unlink()

        return jsonify(
            success=True,
            transcript=transcript
        )

    except Exception as exc:

        # Delete the temporary file even if an error occurs
        if save_path and save_path.exists():
            save_path.unlink()

        return jsonify(
            success=False,
            error=str(exc)
        ), 500