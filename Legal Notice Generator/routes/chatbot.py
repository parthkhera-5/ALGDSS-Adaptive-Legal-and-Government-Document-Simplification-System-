# # from flask import (Blueprint,request,jsonify,render_template)
# # from rag.rag_utils import similarity_search
# # chatbot_bp = Blueprint("chatbot",__name__)
# # # ============================================================
# # # CHAT PAGE
# # # ============================================================
# # @chatbot_bp.route("/chat",methods=["GET"])
# # def chat_page():
# #     return render_template("chat.html")
# # # ============================================================
# # # CHAT API
# # # ============================================================
# # @chatbot_bp.route("/api/chat",methods=["POST"])
# # def chat_api():
# #     try:
# #         data = request.get_json(silent=True) or {}
# #         question = data.get("question","").strip()
# #         print("\n==============================")
# #         print("CHAT QUESTION:", question)
# #         print("==============================")
# #         if not question:
# #             return jsonify({
# #                 "success": False,
# #                 "error": "Question is required."
# #             }), 400
# #         # ----------------------------------------------------
# #         # RAG SEARCH
# #         # ----------------------------------------------------
# #         documents = similarity_search(question,k=5)
# #         print("Retrieved documents:",len(documents))
# #         # ----------------------------------------------------
# #         # No results
# #         # ----------------------------------------------------
# #         if not documents:
# #             return jsonify({
# #                 "success": True,
# #                 "answer":
# #                     "I couldn't find a relevant legal document in the knowledge base.",
# #                 "template": None
# #             })

# #         # ----------------------------------------------------
# #         # Find template
# #         # ----------------------------------------------------
# #         template = None
# #         for document in documents:
# #             print("Retrieved:",document.metadata)
# #             template_id = document.metadata.get("template_id")
# #             document_name = document.metadata.get("document_name")
# #             document_type = document.metadata.get("document_type")
# #             if template_id:
# #                 template = {
# #                     "template_id": template_id,
# #                     "document_name": document_name,
# #                     "document_type": document_type
# #                 }
# #                 break
# #         # ----------------------------------------------------
# #         # Response
# #         # ----------------------------------------------------
# #         if template:
# #             answer = (f"I found a suitable legal document: " f"{template['document_name']}.")
# #         else:
# #             answer = ("I found relevant information, " "but could not identify a document template.")
# #         return jsonify({
# #             "success": True,
# #             "answer": answer,
# #             "template": template
# #         })
# #     except Exception as exc:
# #         print("\nCHAT API ERROR:")
# #         print(exc)
# #         return jsonify({
# #             "success": False,
# #             "error": str(exc)
# #         }), 500







# from flask import Blueprint, request, jsonify, render_template
# from rag.rag_utils import similarity_search, match_document

# chatbot_bp = Blueprint("chatbot", __name__)

# # ============================================================
# # CHAT PAGE
# # ============================================================

# @chatbot_bp.route("/chat", methods=["GET"])
# def chat_page():
#     return render_template("chat.html")


# # ============================================================
# # CHAT API
# # ============================================================

# @chatbot_bp.route("/api/chat", methods=["POST"])
# def chat_api():
#     try:
#         data = request.get_json(silent=True) or {}
#         question = data.get("question", "").strip()

#         print("\n==============================")
#         print("CHAT QUESTION:", question)
#         print("==============================")

#         if not question:
#             return jsonify({
#                 "success": False,
#                 "error": "Question is required."
#             }), 400

#         # ----------------------------------------------------
#         # Match requested document first
#         # ----------------------------------------------------

#         matched_document = match_document(question)

#         if not matched_document:
#             return jsonify({
#                 "success": True,
#                 "answer": "This document is not available in the legal knowledge base.",
#                 "template": None
#             })

#         # ----------------------------------------------------
#         # Search Chroma using matched document name
#         # ----------------------------------------------------

#         documents = similarity_search(matched_document, k=1)

#         print("Retrieved documents:", len(documents))

#         if not documents:
#             return jsonify({
#                 "success": True,
#                 "answer": "This document is not available in the legal knowledge base.",
#                 "template": None
#             })

#         # ----------------------------------------------------
#         # Validate retrieved document
#         # ----------------------------------------------------

#         document = documents[0]

#         template = {
#             "template_id": document.metadata.get("template_id"),
#             "document_name": document.metadata.get("document_name"),
#             "document_type": document.metadata.get("document_type")
#         }

#         retrieved_name = (template["document_name"] or "").lower().strip()

#         if retrieved_name != matched_document.lower():
#             return jsonify({
#                 "success": True,
#                 "answer": "This document is not available in the legal knowledge base.",
#                 "template": None
#             })

#         # ----------------------------------------------------
#         # Success
#         # ----------------------------------------------------

#         return jsonify({
#             "success": True,
#             "answer": f"I found the requested legal document: {template['document_name']}.",
#             "template": template
#         })

#     except Exception as exc:
#         print("\nCHAT API ERROR:")
#         print(exc)

#         return jsonify({
#             "success": False,
#             "error": str(exc)
#         }), 500












from flask import Blueprint, request, jsonify, render_template
from rag.rag_chain import ask_question
chatbot_bp = Blueprint("chatbot", __name__)

# ==========================================================
# Chat Page
# ==========================================================
@chatbot_bp.route("/chat", methods=["GET"])
def chat_page():
    return render_template("chat.html")
# ==========================================================
# Chat API
# ==========================================================
@chatbot_bp.route("/api/chat", methods=["POST"])
def chat_api():

    try:

        data = request.get_json(silent=True) or {}

        question = data.get("question", "").strip()
        language = data.get("language", "en")

        print(f"[CHAT] Language: {language}")
        print(f"[CHAT] Question: {question}")

        if not question:

            return jsonify(
                success=False,
                error="Question is required."
            ), 400

        answer, document = ask_question(
            question=question,
            language=language
        )

        if document is None:

            return jsonify(
                success=True,
                answer=answer,
                template=None
            )

        return jsonify(
            success=True,
            answer=answer,
            template={
                "template_id": document.metadata.get("template_id"),
                "document_name": document.metadata.get("document_name"),
                "document_type": document.metadata.get("document_type"),
            }
        )

    except Exception as exc:

        print(f"Chat API Error: {exc}")

        return jsonify(
            success=False,
            error=str(exc)
        ), 500