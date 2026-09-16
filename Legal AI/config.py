import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    # API
    GROQ_API_KEY = os.getenv("GROQ_API_KEY")
    HF_TOKEN = os.getenv("HF_TOKEN")


        # Language
    SUPPORTED_LANGUAGES = {
        "en": "English",
        "hi": "Hindi"
    }

    DEFAULT_LANGUAGE = "en"
    
    # Embeddings
    EMBEDDING_MODEL = "BAAI/bge-small-en-v1.5"
    
    # Retrieval
    TOP_K = 3
    NEIGHBOR_COUNT = 1

    # Query expansion
    ENABLE_QUERY_EXPANSION = True
    MAX_QUERY_TERMS = 8

    # Upload
    MAX_FILE_SIZE_MB = 2

    RETRIEVAL_THRESHOLD = 0.65

    KNOWLEDGE_RERANKER_THRESHOLD = -5.0

        # Reranker
    RERANKER_MODEL = "cross-encoder/ms-marco-MiniLM-L-6-v2"
   # Context Selection
    MAX_CONTEXT_CHUNKS = 6
    MIN_CONTEXT_CHUNKS = 2
    RERANK_SCORE_MARGIN = 5.0
    RERANKER_THRESHOLD = -10.0


    # GROQ_MODEL = "llama-3.3-70b-versatile"
    GROQ_MODEL = "openai/gpt-oss-120b"
    # GROQ_MODEL = "openai/gpt-oss-20b"

    
    KNOWLEDGE_DATASET_PATH = (
    "dataset/json/legal_knowledge_clean.json"
    )

    KNOWLEDGE_TOP_K = 5

    KNOWLEDGE_INDEX_PATH = "knowledge_base/knowledge.index"
    KNOWLEDGE_RECORDS_PATH = "knowledge_base/knowledge_records.json"
    # Knowledge routing
    ENABLE_KNOWLEDGE_ROUTING = True


