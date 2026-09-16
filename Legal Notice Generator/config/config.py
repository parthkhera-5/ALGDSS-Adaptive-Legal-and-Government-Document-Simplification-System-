import os
from pathlib import Path
from dotenv import load_dotenv
# ---------------------------------------------------------
# Project Root
# ---------------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent.parent
# Load .env
load_dotenv(BASE_DIR / ".env")
# ---------------------------------------------------------
# API Configuration
# ---------------------------------------------------------
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
LLM_MODEL = os.getenv("LLM_MODEL","openai/gpt-oss-120b")
TEMPERATURE = float(os.getenv("TEMPERATURE", "0"))
# ---------------------------------------------------------
# Embedding Configuration
# ---------------------------------------------------------
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL","BAAI/bge-small-en-v1.5")
# ---------------------------------------------------------
# Vector Database
# ---------------------------------------------------------
CHROMA_PATH = BASE_DIR / os.getenv("CHROMA_PATH","database/chroma")
COLLECTION_NAME = os.getenv("COLLECTION_NAME","legal_documents")
TOP_K = int(os.getenv("TOP_K", "5"))
# ---------------------------------------------------------
# Data Directories
# ---------------------------------------------------------
DATA_DIR = BASE_DIR / "data"
TEMPLATE_DIR = DATA_DIR / "templates"
ORIGINAL_DIR = DATA_DIR / "original"
DATA_METADATA_DIR = DATA_DIR / "metadata"
# ---------------------------------------------------------
# Generated Documents
# ---------------------------------------------------------
GENERATED_DIR = BASE_DIR / "generated"
BLANK_DIR = BASE_DIR / "generated" / "blank"
FILLED_DIR = BASE_DIR / "generated" / "filled"
BLANK_DIR.mkdir(parents=True,exist_ok=True)
FILLED_DIR.mkdir(parents=True,exist_ok=True)
# ---------------------------------------------------------
# Upload Configuration
# ---------------------------------------------------------
UPLOAD_FOLDER = ORIGINAL_DIR
ALLOWED_EXTENSIONS = {"pdf","docx","txt"}
# ---------------------------------------------------------
# Document Processing
# ---------------------------------------------------------
CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", "800"))
CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", "150"))
# ---------------------------------------------------------
# Flask Configuration
# ---------------------------------------------------------
SECRET_KEY = os.getenv("SECRET_KEY","legal-document-generator-secret")
MAX_CONTENT_LENGTH = 16 * 1024 * 1024
# ---------------------------------------------------------
# Create Required Directories
# ---------------------------------------------------------
for directory in [CHROMA_PATH,TEMPLATE_DIR,ORIGINAL_DIR,DATA_METADATA_DIR,BLANK_DIR,FILLED_DIR]:
    directory.mkdir(parents=True,exist_ok=True)