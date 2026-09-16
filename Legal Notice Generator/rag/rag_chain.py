# # from langchain_groq import ChatGroq
# # from langchain_core.prompts import PromptTemplate
# # from langchain_core.output_parsers import StrOutputParser
# # from config.config import (GROQ_API_KEY,LLM_MODEL,TEMPERATURE)
# # from rag.rag_utils import (get_retriever,documents_to_context)
# # from rag.prompts import (LEGAL_QA_PROMPT,DOCUMENT_GENERATION_PROMPT)
# # # ---------------------------------------------------------
# # # LLM
# # # ---------------------------------------------------------
# # def get_llm():
# #     if not GROQ_API_KEY:
# #         raise ValueError("GROQ_API_KEY is missing in .env")
# #     return ChatGroq(api_key=GROQ_API_KEY,model=LLM_MODEL,temperature=TEMPERATURE)
# # # ---------------------------------------------------------
# # # Question Answering
# # # ---------------------------------------------------------
# # def ask_question(question):
# #     retriever = get_retriever()
# #     documents = retriever.invoke(question)
# #     if not documents:
# #         return (
# #             "I couldn't find this information "
# #             "in the legal knowledge base."
# #         )
# #     context = documents_to_context(documents)
# #     prompt = PromptTemplate(template=LEGAL_QA_PROMPT,input_variables=["context","question"])
# #     chain = (prompt | get_llm() | StrOutputParser())
# #     return chain.invoke(
# #         {
# #             "context": context,
# #             "question": question
# #         }
# #     )
# # # ---------------------------------------------------------
# # # Generate Legal Document
# # # ---------------------------------------------------------
# # def generate_legal_content(document_type,user_data):
# #     query = (f"Legal requirements and template " f"information for {document_type}")
# #     retriever = get_retriever()
# #     documents = retriever.invoke(query)
# #     context = documents_to_context(documents)
# #     prompt = PromptTemplate(
# #         template=DOCUMENT_GENERATION_PROMPT,
# #         input_variables=["context", "user_data", "document_type"]
# #     )
# #     chain = (prompt | get_llm() | StrOutputParser())
# #     return chain.invoke(
# #         {
# #             "context": context,
# #             "user_data": str(user_data),
# #             "document_type": document_type
# #         }
# #     )


















# from langchain_groq import ChatGroq
# from langchain_core.prompts import PromptTemplate
# from langchain_core.output_parsers import StrOutputParser

# from config.config import GROQ_API_KEY, LLM_MODEL, TEMPERATURE
# from rag.rag_utils import retrieve_documents, documents_to_context
# from rag.prompts import LEGAL_QA_PROMPT, DOCUMENT_GENERATION_PROMPT
# # ---------------------------------------------------------
# # LLM
# # ---------------------------------------------------------

# llm = ChatGroq(api_key=GROQ_API_KEY,model=LLM_MODEL,temperature=TEMPERATURE,)
# # ---------------------------------------------------------
# # Normalize text
# # ---------------------------------------------------------
# def normalize(text):
#     return (text.lower().replace("-", " ").replace("_", " ").strip())
# # ---------------------------------------------------------
# # Validate retrieved document
# # ---------------------------------------------------------
# def is_matching_document(query, document):
#     """
#     Ensure the retrieved document actually matches
#     the user's requested document.
#     """
#     query = normalize(query)
#     name = normalize(document.metadata.get("document_name", ""))
#     doc_type = normalize(document.metadata.get("document_type", ""))
#     template_id = normalize(document.metadata.get("template_id", ""))
#     if name in query or query in name:
#         return True
#     if doc_type and (doc_type in query or query in doc_type):
#         return True
#     if template_id and query == template_id:
#         return True
#     return False
# # ---------------------------------------------------------
# # Question Answering (RAG)
# # ---------------------------------------------------------
# def ask_question(question, language = "en"):
#     """
#     Retrieve a legal document and answer only
#     from the retrieved context.
#     """
#     docs = retrieve_documents(question)
#     if not docs:
#         return None, None
#     best_doc = docs[0]
#     if not is_matching_document(question, best_doc):
#         return None, None
#     context = documents_to_context(docs)
#     prompt = PromptTemplate(template=LEGAL_QA_PROMPT,input_variables=["context", "question"],)
#     chain = prompt | llm | StrOutputParser()
#     answer = chain.invoke(
#         {
#             "context": context,
#             "question": question,
#         }
#     )
#     return answer, best_doc
# # ---------------------------------------------------------
# # Legal Document Generation
# # ---------------------------------------------------------
# def generate_legal_content(document_type, user_data):
#     docs = retrieve_documents(document_type)
#     if not docs:
#         return None
#     context = documents_to_context(docs)
#     prompt = PromptTemplate(
#         template=DOCUMENT_GENERATION_PROMPT,
#         input_variables=["context", "user_data", "document_type"],
#     )
#     chain = prompt | llm | StrOutputParser()
#     return chain.invoke({
#         "context": context,
#         "user_data": str(user_data),
#         "document_type": document_type,
#     })






























from langchain_groq import ChatGroq
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser

from config.config import GROQ_API_KEY, LLM_MODEL, TEMPERATURE
from rag.rag_utils import retrieve_documents, documents_to_context
from rag.prompts import LEGAL_QA_PROMPT, DOCUMENT_GENERATION_PROMPT

# ---------------------------------------------------------
# LLM
# ---------------------------------------------------------

llm = ChatGroq(
    api_key=GROQ_API_KEY,
    model=LLM_MODEL,
    temperature=TEMPERATURE,
)

# ---------------------------------------------------------
# Normalize text
# ---------------------------------------------------------

def normalize(text):
    return (
        text.lower()
        .replace("-", " ")
        .replace("_", " ")
        .strip()
    )

# ---------------------------------------------------------
# Validate retrieved document
# ---------------------------------------------------------

def is_matching_document(query, document):
    """
    Ensure the retrieved document actually matches
    the user's requested document.
    """

    query = normalize(query)

    name = normalize(document.metadata.get("document_name", ""))
    doc_type = normalize(document.metadata.get("document_type", ""))
    template_id = normalize(document.metadata.get("template_id", ""))

    aliases = [
        normalize(alias)
        for alias in document.metadata.get("aliases", [])
    ]

    if name in query or query in name:
        return True

    if doc_type and (doc_type in query or query in doc_type):
        return True

    if template_id and query == template_id:
        return True

    for alias in aliases:
        if alias in query or query in alias:
            return True

    return False

# ---------------------------------------------------------
# Question Answering (RAG)
# ---------------------------------------------------------

def ask_question(question, language="en"):
    """
    Retrieve a legal document and answer
    only from the retrieved context.
    """

    docs = retrieve_documents(question)

    if not docs:

        if language == "hi":
            return (
                "क्षमा करें, यह दस्तावेज़ कानूनी ज्ञान आधार में उपलब्ध नहीं है।",
                None,
            )

        return (
            "Sorry, this document is not available in the legal knowledge base.",
            None,
        )

    best_doc = docs[0]

    from rag.rag_utils import normalize_multilingual_query

    normalized_question = normalize_multilingual_query(question)

    if not is_matching_document(normalized_question, best_doc):
        
        if language == "hi":
            return (
                "क्षमा करें, यह दस्तावेज़ कानूनी ज्ञान आधार में उपलब्ध नहीं है।",
                None,
            )

        return (
            "Sorry, this document is not available in the legal knowledge base.",
            None,
        )

    context = documents_to_context(docs)

    # -----------------------------------------------------
    # Language instruction
    # -----------------------------------------------------

    if language == "hi":

        language_instruction = """
        You are a Legal Document Assistant.

        Reply completely in Hindi using simple and natural language.

        Keep legal document names understandable.
        Example:
        - Affidavit (शपथ पत्र)
        - Rent Agreement (किराया समझौता)
        - General Legal Notice (सामान्य कानूनी नोटिस)

        Do not translate template IDs.
        """

    else:

        language_instruction = """
        You are a Legal Document Assistant.

        Reply completely in English.
        """

    # -----------------------------------------------------
    # Dynamic prompt
    # -----------------------------------------------------

    prompt = PromptTemplate(
        template=f"{language_instruction}\n\n{LEGAL_QA_PROMPT}",
        input_variables=["context", "question"],
    )

    chain = prompt | llm | StrOutputParser()

    answer = chain.invoke(
        {
            "context": context,
            "question": question,
        }
    )

    return answer, best_doc

# ---------------------------------------------------------
# Legal Document Generation
# ---------------------------------------------------------

def generate_legal_content(document_type, user_data):

    docs = retrieve_documents(document_type)

    if not docs:
        return None

    context = documents_to_context(docs)

    prompt = PromptTemplate(
        template=DOCUMENT_GENERATION_PROMPT,
        input_variables=[
            "context",
            "user_data",
            "document_type",
        ],
    )

    chain = prompt | llm | StrOutputParser()

    return chain.invoke(
        {
            "context": context,
            "user_data": str(user_data),
            "document_type": document_type,
        }
    )