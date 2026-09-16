import json
from pathlib import Path
from config.config import (DATA_METADATA_DIR,TEMPLATE_DIR)
# ============================================================
# LOAD ALL TEMPLATE METADATA
# ============================================================
def load_template_metadata():
    """
    Load metadata from all JSON files inside:
        data/metadata/
    Each JSON file describes one legal document template.
    """
    templates = []
    if not DATA_METADATA_DIR.exists():
        print(f"Metadata directory not found: " f"{DATA_METADATA_DIR}")
        return templates
    for file_path in DATA_METADATA_DIR.glob("*.json"):
        try:
            with open(file_path, "r", encoding="utf-8") as file:
                data = json.load(file)
            # ------------------------------------------------
            # Store metadata filename
            # ------------------------------------------------
            data.setdefault("metadata_file", file_path.name)
            # ------------------------------------------------
            # Make sure template_id exists
            # ------------------------------------------------
            if not data.get("template_id"):
                data["template_id"] = file_path.stem
            # ------------------------------------------------
            # Make sure template_file points to DOCX template
            #
            # If JSON already contains template_file,
            # use it.
            #
            # Otherwise try to find a DOCX file automatically.
            # ------------------------------------------------
            template_file = data.get("template_file")
            if template_file:
                template_path = (TEMPLATE_DIR / template_file)
                if template_path.exists():
                    data["template_file"] = (template_path.name)
                else:
                    print(f"Warning: Template file not found: " f"{template_path}")
            else:
                # ------------------------------------------------
                # Try to find DOCX template automatically
                # based on metadata filename.
                # ------------------------------------------------
                possible_name = (file_path.stem + "_2026_template.docx")
                possible_path = (TEMPLATE_DIR / possible_name)
                if possible_path.exists():
                    data["template_file"] = (possible_path.name)
                else:
                    print(f"Warning: No DOCX template configured " f"for {file_path.name}")
            templates.append(data)
        except (json.JSONDecodeError, OSError) as error:
            print(f"Error reading metadata file " f"{file_path.name}: {error}")
    return templates
# ============================================================
# GET TEMPLATE BY ID
# ============================================================
def get_template(template_id):
    """
    Return a template metadata dictionary using template_id.
    """
    templates = load_template_metadata()
    for template in templates:
        if (str(template.get("template_id")).strip()==str(template_id).strip()):
            return template
    return None
# ============================================================
# GET TEMPLATE NAMES / IDS
# ============================================================
def get_template_names():
    """
    Return all available template IDs.
    """
    templates = load_template_metadata()
    return [
        template.get("template_id")
        for template in templates
        if template.get("template_id")
    ]
# ============================================================
# GET TEMPLATE FIELDS
# ============================================================
def get_template_fields(template_id):
    """
    Return the fields required by a specific template.
    """
    template = get_template(template_id)
    if not template:
        return []
    return template.get("fields",[])
# ============================================================
# GET TEMPLATE METADATA
# ============================================================
def get_template_metadata(template_id):
    """
    Return complete metadata for a specific template.
    """
    return get_template(template_id)
# ============================================================
# GET ALL TEMPLATES
# ============================================================
def get_all_templates():
    """
    Return metadata for all available templates.
    """
    return load_template_metadata()