import os
import tempfile

from flask import Flask, request, jsonify, render_template, send_file
from gtts import gTTS
from groq import Groq

from document import DocumentProcessor
from legal_engine import LegalEngine
from config import Config

# ============================================================
# FLASK APP
# ============================================================

app = Flask(__name__)

# ============================================================
# GROQ CLIENT
# ============================================================

groq_client = Groq(
    api_key=Config.GROQ_API_KEY
)
# Maximum upload size: 10 MB
app.config["MAX_CONTENT_LENGTH"] = 10 * 1024 * 1024


# ============================================================
# LEGAL ENGINE
# ============================================================

engine = LegalEngine()


# ============================================================
# HOME
# ============================================================

@app.route("/", methods=["GET"])
def home():

    return render_template("index.html")

# ============================================================
# UPLOAD DOCUMENT
# ============================================================

@app.route("/upload", methods=["POST"])
def upload():

    # --------------------------------------------------------
    # Check file
    # --------------------------------------------------------

    if "file" not in request.files:

        return jsonify({
            "error": "No file uploaded."
        }), 400

    file = request.files["file"]

    if file.filename == "":

        return jsonify({
            "error": "No file selected."
        }), 400


    # --------------------------------------------------------
    # Create temporary file
    # --------------------------------------------------------

    temp_path = None

    try:

        # Preserve original extension
        _, extension = os.path.splitext(
            file.filename
        )

        with tempfile.NamedTemporaryFile(
            delete=False,
            suffix=extension
        ) as temp_file:

            file.save(
                temp_file.name
            )

            temp_path = temp_file.name


        # ----------------------------------------------------
        # Process document
        # ----------------------------------------------------

        processor = DocumentProcessor()

        records = processor.process(
            temp_path
        )


        if not records:

            return jsonify({
                "error": (
                    "No readable content found "
                    "in the document."
                )
            }), 400


        # ----------------------------------------------------
        # Load into Legal Engine
        # ----------------------------------------------------

        engine.load_document(
            records
        )


        # ----------------------------------------------------
        # Success
        # ----------------------------------------------------

        return jsonify({

            "message":
                "Document loaded successfully.",

            "records":
                len(records),

            "document_loaded":
                engine.loaded

        }), 200


    except Exception as e:

        return jsonify({
            "error": str(e)
        }), 500


    finally:

        # ----------------------------------------------------
        # Delete temporary document
        # ----------------------------------------------------

        if temp_path and os.path.exists(
            temp_path
        ):

            try:

                os.remove(
                    temp_path
                )

            except Exception:
                pass


# ============================================================
# CHAT
# ============================================================

# ============================================================
# CHAT
# ============================================================

@app.route("/chat", methods=["POST"])
def chat():

    # --------------------------------------------------------
    # Validate JSON
    # --------------------------------------------------------

    data = request.get_json()

    if not data:

        return jsonify({
            "error": "Invalid JSON."
        }), 400


    # --------------------------------------------------------
    # Get query
    # --------------------------------------------------------

    query = data.get(
        "query",
        ""
    )

    if not isinstance(
        query,
        str
    ):

        return jsonify({
            "error": "Query must be a string."
        }), 400


    query = query.strip()


    if not query:

        return jsonify({
            "error": "Query is required."
        }), 400


    # --------------------------------------------------------
    # Get operation
    # --------------------------------------------------------

    operation = data.get(
    "operation",
    "DOCUMENT_QA"
    )

    if not isinstance(
        operation,
        str
    ):

        return jsonify({
            "error": "Operation must be a string."
        }), 400

    operation = operation.strip().upper()


    # --------------------------------------------------------
    # Get language
    # --------------------------------------------------------

    language = data.get(
        "language",
        "en"
    )

    if not isinstance(
        language,
        str
    ):

        return jsonify({
            "error": "Language must be a string."
        }), 400

    language = language.strip().lower()


    # --------------------------------------------------------
    # Validate language
    # --------------------------------------------------------

    if language not in {
        "en",
        "hi"
    }:

        return jsonify({
            "error": "Unsupported language. Use 'en' or 'hi'."
        }), 400

    # --------------------------------------------------------
    # Ask Legal Engine
    # --------------------------------------------------------

    try:

        result = engine.ask(
            query=query,
            operation=operation,
            language=language
        )

        return jsonify(
            result
        ), 200


    except Exception as e:

        return jsonify({
            "error": str(e)
        }), 500

# ============================================================
# TEXT TO SPEECH
# ============================================================

@app.route("/tts", methods=["POST"])
def text_to_speech():

    # --------------------------------------------------------
    # Validate JSON
    # --------------------------------------------------------

    data = request.get_json()

    if not data:

        return jsonify({
            "error": "Invalid JSON."
        }), 400


    # --------------------------------------------------------
    # Get text
    # --------------------------------------------------------

    text = data.get(
        "text",
        ""
    )

    if not isinstance(
        text,
        str
    ):

        return jsonify({
            "error": "Text must be a string."
        }), 400


    text = text.strip()

    # --------------------------------------------------------
    # Get language
    # --------------------------------------------------------

    language = data.get(
        "language",
        "en"
    )

    if not isinstance(
        language,
        str
    ):

        return jsonify({
            "error": "Language must be a string."
        }), 400


    language = language.strip().lower()


    # --------------------------------------------------------
    # Validate language
    # --------------------------------------------------------

    if language not in {
        "en",
        "hi"
    }:

        return jsonify({
            "error": "Unsupported language. Use 'en' or 'hi'."
        }), 400

    if not text:

        return jsonify({
            "error": "Text is required."
        }), 400


    # --------------------------------------------------------
    # Generate speech
    # --------------------------------------------------------

    temp_path = None

    try:

        with tempfile.NamedTemporaryFile(
            delete=False,
            suffix=".mp3"
        ) as temp_file:

            temp_path = temp_file.name


        tts = gTTS(
            text=text,
            lang=language,
            slow=False
        )

        tts.save(
            temp_path
        )


        # ----------------------------------------------------
        # Send audio to browser
        # ----------------------------------------------------

        return send_file(
            temp_path,
            mimetype="audio/mpeg",
            as_attachment=False
        )


    except Exception as e:

        if temp_path and os.path.exists(
            temp_path
        ):

            try:
                os.remove(temp_path)
            except Exception:
                pass


        return jsonify({
            "error": str(e)
        }), 500







# ============================================================
# SPEECH TO TEXT
# Browser Audio → Groq Whisper → Text
# ============================================================

@app.route("/speech-to-text", methods=["POST"])
def speech_to_text():

    # --------------------------------------------------------
    # Check audio file
    # --------------------------------------------------------

    if "audio" not in request.files:

        return jsonify({
            "error": "No audio file uploaded."
        }), 400


    audio_file = request.files["audio"]


    if audio_file.filename == "":

        return jsonify({
            "error": "No audio file selected."
        }), 400


    # --------------------------------------------------------
    # Get language
    # --------------------------------------------------------

    language = request.form.get(
        "language",
        ""
    ).strip().lower()


    # --------------------------------------------------------
    # Validate language
    # --------------------------------------------------------

    if language not in {
        "",
        "en",
        "hi"
    }:

        return jsonify({
            "error": (
                "Unsupported language. "
                "Use 'en', 'hi', or leave empty "
                "for automatic detection."
            )
        }), 400


    # --------------------------------------------------------
    # Save temporary audio
    # --------------------------------------------------------

    temp_path = None

    try:

        with tempfile.NamedTemporaryFile(
            delete=False,
            suffix=".webm"
        ) as temp_file:

            audio_file.save(
                temp_file.name
            )

            temp_path = temp_file.name


        # ----------------------------------------------------
        # Send audio to Groq
        # ----------------------------------------------------

        with open(
            temp_path,
            "rb"
        ) as file:

            transcription = (
                groq_client
                .audio
                .transcriptions
                .create(

                    file=file,

                    model="whisper-large-v3-turbo",

                    # Empty language means automatic detection
                    language=(
                        language
                        if language
                        else None
                    ),

                    response_format="json",

                    temperature=0.0
                )
            )


        # ----------------------------------------------------
        # Get transcription
        # ----------------------------------------------------

        text = transcription.text.strip()


        if not text:

            return jsonify({
                "error": "No speech detected."
            }), 400


        # ----------------------------------------------------
        # Return text to frontend
        # ----------------------------------------------------

        return jsonify({

            "text": text,

            "language":
                language if language else "auto"

        }), 200


    except Exception as e:

        return jsonify({
            "error": str(e)
        }), 500


    finally:

        # ----------------------------------------------------
        # Delete temporary audio
        # ----------------------------------------------------

        if temp_path and os.path.exists(
            temp_path
        ):

            try:

                os.remove(
                    temp_path
                )

            except Exception:
                pass



            
    
# ============================================================
# HEALTH CHECK
# ============================================================

@app.route("/health", methods=["GET"])
def health():

    return jsonify({

        "status": "ok",

        "document_loaded":
            engine.loaded,

         "knowledge_loaded":
            (
                engine.knowledge_retriever.index
                is not None
            )

    })


# ============================================================
# RUN
# ============================================================

if __name__ == "__main__":

    app.run(
        host="127.0.0.1",
        port=5000,
        debug=True
    )
