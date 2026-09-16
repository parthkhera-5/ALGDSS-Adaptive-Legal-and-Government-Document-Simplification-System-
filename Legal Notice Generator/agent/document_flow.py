# from document_generator.generator import (generate_from_template,create_document_from_text)
# from metadata.metadata import (get_template)
# from rag.rag_chain import (generate_legal_content)

# def generate_document(document_type,user_data,use_template=True):
#     """
#     Main document-generation workflow.
#     Flow:
#     User Input
#         ↓
#     Template Selection
#         ↓
#     RAG Retrieval
#         ↓
#     LLM Processing
#         ↓
#     DOCX Generation
#     """
#     template = get_template(document_type)
#     # -----------------------------------------------------
#     # Template based generation
#     # -----------------------------------------------------
#     if use_template and template:
#         template_file = template.get("template_file")
#         if template_file:
#             return generate_from_template(template_file,user_data)
#     # -----------------------------------------------------
#     # AI generated document
#     # -----------------------------------------------------
#     generated_content = generate_legal_content(document_type,user_data)
#     return create_document_from_text(generated_content,title=document_type)










from document_generator.generator import (generate_from_template,create_document_from_text,)
from metadata.metadata import get_template
from rag.rag_chain import generate_legal_content
# ==========================================================
# Main Document Generation Flow
# ==========================================================
def generate_document(document_type, user_data, use_template=True):
    """
    Workflow

    User Request
        ↓
    Retrieve from ChromaDB
        ↓
    Validate document exists
        ↓
    Generate DOCX
    """
    # ------------------------------------------------------
    # Template-based generation
    # ------------------------------------------------------
    template = get_template(document_type)
    if use_template and template:
        template_file = template.get("template_file")
        if template_file:
            return generate_from_template(template_name=template_file,data=user_data,)
    # ------------------------------------------------------
    # RAG + LLM generation
    # ------------------------------------------------------
    generated_content = generate_legal_content(document_type=document_type,user_data=user_data,)
    if generated_content is None:
        raise ValueError("This document is not available in the legal knowledge base.")
    return create_document_from_text(text=generated_content,title=document_type,)