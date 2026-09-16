import os
import sys
from pathlib import Path
import pytest
# ---------------------------------------------------------
# Add project root to Python path
# ---------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0,str(PROJECT_ROOT))
# --------------------------------------------------------
# Configuration Tests
# ---------------------------------------------------------
def test_project_directories():
    from config.config import (TEMPLATE_DIR,ORIGINAL_DIR,CHROMA_PATH,FILLED_DIR)
    assert TEMPLATE_DIR.exists()
    assert ORIGINAL_DIR.exists()
    assert CHROMA_PATH.exists()
    assert FILLED_DIR.exists()

# ---------------------------------------------------------
# Utility Tests
# ---------------------------------------------------------
def test_clean_text():
    from utils.utils import clean_text
    result = clean_text("Hello    Legal     Document")
    assert result == ("Hello Legal Document")
# ---------------------------------------------------------
# Template Metadata Test
# ---------------------------------------------------------
def test_template_metadata():
    from metadata.metadata import (load_template_metadata)
    templates = load_template_metadata()
    assert isinstance(templates,list)
# ---------------------------------------------------------
# Flask Test
# ---------------------------------------------------------
def test_flask_app():
    from app import app
    app.config["TESTING"] = True
    client = app.test_client()
    response = client.get("/health")
    assert response.status_code == 200
    data = response.get_json()
    assert data["status"] == "ok"
# ---------------------------------------------------------
# Document Generator Test
# ---------------------------------------------------------
def test_blank_document():
    from document_generator.generator import (create_blank_document)
    path = create_blank_document(title="Test Legal Document")
    assert path.exists()
    # Clean test file
    if path.exists():
        path.unlink()