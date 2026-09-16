from flask import (Blueprint,request,jsonify,send_file)
from werkzeug.utils import secure_filename
from config.config import (ORIGINAL_DIR,ALLOWED_EXTENSIONS,BLANK_DIR,FILLED_DIR)
from document_generator.generator import (load_docx_template,replace_placeholders_with_lines)
from rag.rag_utils import retrieve_documents

documents_bp = Blueprint("documents",__name__)
# ============================================================
# ALLOWED FILE CHECK
# ============================================================
def allowed_file(filename):
    return ("." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS)
# ============================================================
# UPLOAD DOCUMENT
# ============================================================
@documents_bp.route("/api/documents/upload",methods=["POST"])
def upload_document():
    if "file" not in request.files:
        return jsonify({
            "success": False,
            "error": "No file uploaded."
        }), 400
    file = request.files["file"]
    if not file.filename:
        return jsonify({
            "success": False,
            "error": "No filename provided."
        }), 400
    if not allowed_file(file.filename):
        return jsonify({
            "success": False,
            "error": "Unsupported file type."
        }), 400
    filename = secure_filename(file.filename)
    output_path = (ORIGINAL_DIR / filename)
    output_path.parent.mkdir(parents=True,exist_ok=True)
    file.save(str(output_path))
    return jsonify({
        "success": True,
        "filename": filename
    })
# ============================================================
# DOWNLOAD GENERATED DOCUMENT
# ============================================================
@documents_bp.route("/api/documents/download",methods=["GET"])
def download_document():
    filename = request.args.get("filename")
    if not filename:
        return jsonify({
            "success": False,
            "error": "Filename is required."
        }), 400
    filename = secure_filename(filename)
    # --------------------------------------------------------
    # Check filled documents first
    # --------------------------------------------------------
    filled_path = (FILLED_DIR / filename)
    if filled_path.exists():
        return send_file(str(filled_path),as_attachment=True,download_name=filename)
    # --------------------------------------------------------
    # Check blank documents
    # --------------------------------------------------------
    blank_path = (BLANK_DIR / filename)
    if blank_path.exists():
        return send_file(str(blank_path),as_attachment=True,download_name=filename)
    # --------------------------------------------------------
    # File not found
    # --------------------------------------------------------
    print(f"Download failed. File not found: {filename}")
    print(f"Checked filled: {filled_path}")
    print(f"Checked blank: {blank_path}")
    return jsonify({
        "success": False,
        "error": "Document not found."
    }), 404
# ============================================================
# GENERATE BLANK DOCUMENT
# ============================================================
@documents_bp.route("/generate/blank",methods=["POST"])
def generate_blank_document():
    try:
        from metadata.metadata import get_template
        data = request.get_json(silent=True) or {}
        template_id = data.get("template_id")
        if not template_id:
            return jsonify({
                "success": False,
                "error": "template_id is required."
            }), 400
        # ----------------------------------------------------
        # Get template metadata
        # ----------------------------------------------------
        template = get_template(template_id)
        if not template:
            return jsonify({
                "success": False,
                "error": "Template not found."
            }), 404
        # ----------------------------------------------------
        # Get DOCX template filename
        # ----------------------------------------------------
        template_file = template.get("template_file")
        if not template_file:
            return jsonify({
                "success": False,
                "error": "Template file is not configured."
            }), 500
        # ----------------------------------------------------
        # Load original DOCX template
        # ----------------------------------------------------
        document = load_docx_template(template_file)
        # ----------------------------------------------------
        # Replace {{placeholders}} with blank lines
        # ----------------------------------------------------
        document = replace_placeholders_with_lines(document)
        # ----------------------------------------------------
        # Generate filename
        # ----------------------------------------------------
        import uuid
        filename = (f"{template_id}_blank_" f"{uuid.uuid4().hex[:8]}.docx")
        output_path = (BLANK_DIR / filename)
        output_path.parent.mkdir(parents=True,exist_ok=True)
        # ----------------------------------------------------
        # Save blank document
        # ----------------------------------------------------
        document.save(str(output_path))
        print(f"Blank document generated: {output_path}")
        return jsonify({
            "success": True,
            "filename": filename
        })
    except Exception as exc:
        print(f"Blank document generation error: {exc}")
        return jsonify({
            "success": False,
            "error": str(exc)
        }), 500
# ============================================================
# VALIDATE DOCUMENT TYPE
# ============================================================

def validate_document_type(document_type):
    """
    Validate that the requested document exists in the
    ChromaDB knowledge base using LangChain Retriever.
    """

    documents = retrieve_documents(document_type)

    if not documents:
        return jsonify({
            "success": False,
            "message": "This document is not available in the legal knowledge base."
        }), 404

    return documents[0].metadata.get("template_id")