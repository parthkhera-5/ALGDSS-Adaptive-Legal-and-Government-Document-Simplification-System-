from pathlib import Path
from flask import (Blueprint,jsonify,render_template,request)
from metadata.metadata import (get_template_metadata,get_template,get_template_fields,get_template_names)
from agent.document_flow import (generate_document)
forms_bp = Blueprint("forms",__name__)

# ============================================================
# FORM PAGE
# ============================================================
# Opens the form for one specific legal document.
#
# Example:
# /form-page/AFF-2026-001
# ============================================================
@forms_bp.route("/form-page/<template_id>",methods=["GET"])
def form_page(template_id):
    metadata = get_template_metadata(template_id)
    if not metadata:
        return ("Template not found",404)
    return render_template("form.html",template_id=template_id)
# ============================================================
# GET FORM FIELDS FOR SPECIFIC DOCUMENT
# ============================================================
# The frontend calls:
#
# GET /form/AFF-2026-001
#
# The backend reads the corresponding metadata JSON and
# returns ONLY the fields required for that document.
# ============================================================
@forms_bp.route("/form/<template_id>",methods=["GET"])
def get_form(template_id):
    metadata = get_template_metadata(template_id)
    if not metadata:
        return jsonify({
            "success": False,
            "error": "Template not found"
        }), 404
    return jsonify({
        "success": True,
        "template_id": metadata["template_id"],
        "document_name": metadata["document_name"],
        "fields": metadata["fields"]
    })

# ============================================================
# API: LIST AVAILABLE TEMPLATES
# ============================================================
@forms_bp.route("/api/templates",methods=["GET"])
def template_list():
    return jsonify({
        "success": True,
        "templates": get_template_names()
    })
# ============================================================
# API: GET TEMPLATE DETAILS
# ============================================================
@forms_bp.route("/api/templates/<template_id>",methods=["GET"])
def template_details(template_id):
    template = get_template(template_id)
    if not template:
        return jsonify({
            "success": False,
            "error":"Template not found."
        }), 404
    return jsonify({
        "success": True,
        "template": template,
        "fields": get_template_fields(template_id)
    })
# ============================================================
# API: GENERATE DOCUMENT
# ============================================================
#
# This is kept for compatibility with the existing
# document-generation workflow.
# ============================================================

@forms_bp.route("/api/generate",methods=["POST"])
def generate():
    try:
        data = request.get_json(silent=True) or {}
        document_type = data.get("document_type")
        user_data = data.get("data",{})
        use_template = data.get("use_template",True)
        if not document_type:
            return jsonify({
                "success": False,
                "error": "document_type is required."
            }), 400
        result = generate_document(document_type=document_type,user_data=user_data,use_template=use_template)
        # -----------------------------------------------
        # result is a Path object
        # -----------------------------------------------
        filename = Path(result).name
        print(f"Generated file: {result}")
        print(f"Returning filename: {filename}")
        return jsonify({
            "success": True,
            "filename": filename
        })
    except Exception as exc:
        print(f"Document generation error: {exc}")
        return jsonify({
            "success": False,
            "error": str(exc)
        }), 500