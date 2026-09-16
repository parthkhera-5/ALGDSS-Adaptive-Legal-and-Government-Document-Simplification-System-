# # from pathlib import Path
# # from langchain_huggingface import HuggingFaceEmbeddings
# # from langchain_chroma import Chroma
# # from langchain_core.documents import Document
# # from langchain_text_splitters import RecursiveCharacterTextSplitter
# # from config.config import (EMBEDDING_MODEL,CHROMA_PATH,COLLECTION_NAME,CHUNK_SIZE,CHUNK_OVERLAP,TOP_K)
# # # ---------------------------------------------------------
# # # Embedding Model
# # # ---------------------------------------------------------
# # _embeddings = None
# # def get_embeddings():
# #     global _embeddings
# #     if _embeddings is None:
# #         _embeddings = HuggingFaceEmbeddings(
# #             model_name=EMBEDDING_MODEL,
# #             model_kwargs={
# #                 "device": "cpu"
# #             },
# #             encode_kwargs={
# #                 "normalize_embeddings": True
# #             }
# #         )
# #     return _embeddings
# # # ---------------------------------------------------------
# # # Text Splitter
# # # ---------------------------------------------------------
# # def get_text_splitter():
# #     return RecursiveCharacterTextSplitter(
# #         chunk_size=CHUNK_SIZE,
# #         chunk_overlap=CHUNK_OVERLAP,
# #         separators=[
# #             "\n\n",
# #             "\n",
# #             ". ",
# #             " ",
# #             ""
# #         ]
# #     )
# # # ---------------------------------------------------------
# # # Chroma Database
# # # ---------------------------------------------------------
# # def get_vectorstore():
# #     return Chroma(
# #         collection_name=COLLECTION_NAME,
# #         persist_directory=str(CHROMA_PATH),
# #         embedding_function=get_embeddings()
# #     )
# # # ---------------------------------------------------------
# # # Create Documents
# # # ---------------------------------------------------------
# # def create_documents(texts,metadatas=None):
# #     documents = []
# #     for index, text in enumerate(texts):
# #         metadata = {}
# #         if metadatas and index < len(metadatas):
# #             metadata = metadatas[index]
# #         documents.append(Document(page_content=text,metadata=metadata))
# #     return documents
# # # ---------------------------------------------------------
# # # Split Documents
# # # ---------------------------------------------------------
# # def split_documents(documents):
# #     splitter = get_text_splitter()
# #     return splitter.split_documents(documents)
# # # ---------------------------------------------------------
# # # Add Documents
# # # ---------------------------------------------------------
# # def add_documents(documents):
# #     vectorstore = get_vectorstore()
# #     vectorstore.add_documents(documents)
# #     return vectorstore
# # # ---------------------------------------------------------
# # # Retriever
# # # ---------------------------------------------------------
# # def get_retriever():
# #     vectorstore = get_vectorstore()
# #     return vectorstore.as_retriever(
# #         search_type="similarity",
# #         search_kwargs={
# #             "k": TOP_K
# #         }
# #     )
# # # ---------------------------------------------------------
# # # Search
# # # ---------------------------------------------------------
# # def similarity_search(query,k=None):
# #     vectorstore = get_vectorstore()
# #     if k is None:
# #         k = TOP_K
# #     return vectorstore.similarity_search(
# #         query,
# #         k=k
# #     )
# # # ---------------------------------------------------------
# # # Extract Context
# # # ---------------------------------------------------------
# # def documents_to_context(documents):
# #     if not documents:
# #         return ""
# #     context_parts = []
# #     for document in documents:
# #         template_id = document.metadata.get("template_id", "unknown")
# #         document_name = document.metadata.get("document_name", "unknown")
# #         context_parts.append(
# #             f"Template ID: {template_id}\n"
# #             f"Document Name: {document_name}\n"
# #             f"{document.page_content}"
# #         )
# #     return "\n\n".join(context_parts)















# # from pathlib import Path
# # from difflib import get_close_matches
# # import re

# # from langchain_huggingface import HuggingFaceEmbeddings
# # from langchain_chroma import Chroma
# # from langchain_core.documents import Document
# # from langchain_text_splitters import RecursiveCharacterTextSplitter

# # from config.config import (
# #     EMBEDDING_MODEL,
# #     CHROMA_PATH,
# #     COLLECTION_NAME,
# #     CHUNK_SIZE,
# #     CHUNK_OVERLAP,
# #     TOP_K
# # )

# # from metadata.metadata import get_all_templates

# # # ---------------------------------------------------------
# # # Embeddings
# # # ---------------------------------------------------------

# # _embeddings = None


# # def get_embeddings():
# #     global _embeddings

# #     if _embeddings is None:
# #         _embeddings = HuggingFaceEmbeddings(
# #             model_name=EMBEDDING_MODEL,
# #             model_kwargs={"device": "cpu"},
# #             encode_kwargs={"normalize_embeddings": True},
# #         )

# #     return _embeddings


# # # ---------------------------------------------------------
# # # Text Splitter
# # # ---------------------------------------------------------

# # def get_text_splitter():
# #     return RecursiveCharacterTextSplitter(
# #         chunk_size=CHUNK_SIZE,
# #         chunk_overlap=CHUNK_OVERLAP,
# #         separators=["\n\n", "\n", ". ", " ", ""],
# #     )


# # # ---------------------------------------------------------
# # # Chroma
# # # ---------------------------------------------------------

# # def get_vectorstore():
# #     return Chroma(
# #         collection_name=COLLECTION_NAME,
# #         persist_directory=str(CHROMA_PATH),
# #         embedding_function=get_embeddings(),
# #     )


# # # ---------------------------------------------------------
# # # Create Documents
# # # ---------------------------------------------------------

# # def create_documents(texts, metadatas=None):
# #     docs = []

# #     for i, text in enumerate(texts):

# #         metadata = {}

# #         if metadatas and i < len(metadatas):
# #             metadata = metadatas[i]

# #         docs.append(Document(page_content=text, metadata=metadata))

# #     return docs


# # # ---------------------------------------------------------
# # # Split Documents
# # # ---------------------------------------------------------

# # def split_documents(documents):
# #     return get_text_splitter().split_documents(documents)


# # # ---------------------------------------------------------
# # # Add Documents
# # # ---------------------------------------------------------

# # def add_documents(documents):
# #     vectorstore = get_vectorstore()
# #     vectorstore.add_documents(documents)
# #     return vectorstore


# # # ---------------------------------------------------------
# # # Dynamic Template Matching
# # # ---------------------------------------------------------

# # # def _normalize(text):
# # #     text = text.lower()

# # #     text = re.sub(
# # #         r"\b(i|need|want|please|give|generate|create|make|me|a|an|the)\b",
# # #         " ",
# # #         text,
# # #     )

# # #     text = re.sub(r"[^a-z0-9 ]", " ", text)

# # #     text = re.sub(r"\s+", " ", text)

# # #     return text.strip()


# # # def get_available_document_names():
# # #     templates = get_all_templates()

# # #     names = []

# # #     for template in templates:
# # #         name = template.get("document_name") or template.get("title")

# # #         if name:
# # #             names.append(name.lower())

# # #     return names


# # # ALIASES = {
# # #     "nda": "non disclosure agreement",
# # #     "noc": "property noc",
# # #     "legal notice": "general legal notice",
# # # }


# # # def match_document(query):
# # #     query = _normalize(query)

# # #     for alias, actual in ALIASES.items():
# # #         if alias in query:
# # #             return actual

# # #     names = get_available_document_names()

# # #     for name in names:
# # #         if name in query:
# # #             return name

# # #     matches = get_close_matches(query, names, n=1, cutoff=0.65)

# # #     if matches:
# # #         return matches[0]

# # #     return None

# # import re
# # from difflib import get_close_matches
# # from metadata.metadata import get_all_templates

# # # ---------------------------------------------------------
# # # Normalize Text
# # # ---------------------------------------------------------

# # def _normalize(text):
# #     text = text.lower()

# #     text = re.sub(
# #         r"\b(i|need|want|please|give|generate|create|make|me|a|an|the|get|show)\b",
# #         " ",
# #         text
# #     )

# #     text = re.sub(r"[^a-z0-9 ]", " ", text)
# #     text = re.sub(r"\s+", " ", text)

# #     return text.strip()


# # # ---------------------------------------------------------
# # # Common aliases
# # # ---------------------------------------------------------

# # ALIASES = {
# #     "nda": "non disclosure agreement",
# #     "noc": "property noc",

# #     "tax certificate": "certificate of taxation",
# #     "taxation certificate": "certificate of taxation",
# #     "certificate of tax": "certificate of taxation",
# #     "tax certificate supreme court": "certificate of taxation",

# #     "non payment notice": "non-payment notice",
# #     "non-payment notice": "non-payment notice",
# #     "payment default notice": "non-payment notice",
# #     "rent default notice": "non-payment notice"
# # }


# # # ---------------------------------------------------------
# # # Dynamic document matching
# # # ---------------------------------------------------------

# # # def match_document(query):

# # #     query = _normalize(query)

# # #     # ---------- aliases ----------
# # #     for alias, target in ALIASES.items():
# # #         if alias in query:
# # #             return target

# # #     templates = get_all_templates()

# # #     document_names = []

# # #     for template in templates:

# # #         name = template.get("document_name")

# # #         if name:
# # #             document_names.append(name.lower())

# # #     # ---------- direct substring ----------
# # #     for name in document_names:
# # #         if name in query:
# # #             return name

# # #     # ---------- keyword overlap ----------
# # #     query_words = set(query.split())

# # #     best_name = None
# # #     best_score = 0

# # #     for name in document_names:

# # #         name_words = set(name.split())

# # #         score = len(query_words & name_words)

# # #         if score > best_score:
# # #             best_score = score
# # #             best_name = name

# # #     if best_score >= 2:
# # #         return best_name

# # #     # ---------- fuzzy fallback ----------
# # #     matches = get_close_matches(query, document_names, n=1, cutoff=0.6)

# # #     if matches:
# # #         return matches[0]

# # #     return None




# # def match_document(query):
# #     query = _normalize(query)

# #     templates = get_all_templates()

# #     candidates = {}

# #     for template in templates:
# #         name = template.get("document_name", "").lower()

# #         if name:
# #             candidates[name] = name

# #         # Read aliases from metadata.json
# #         for alias in template.get("aliases", []):
# #             alias = alias.lower().strip()
# #             candidates[alias] = name

# #     # 1. Exact alias or name
# #     if query in candidates:
# #         return candidates[query]

# #     # 2. Substring match
# #     for phrase, actual in candidates.items():
# #         if phrase in query:
# #             return actual

# #     # 3. Keyword overlap
# #     query_words = set(query.split())

# #     best_name = None
# #     best_score = 0

# #     for phrase, actual in candidates.items():
# #         phrase_words = set(phrase.split())
# #         score = len(query_words & phrase_words)

# #         if score > best_score:
# #             best_score = score
# #             best_name = actual

# #     if best_score >= 1:
# #         return best_name

# #     # 4. Fuzzy fallback
# #     matches = get_close_matches(query, list(candidates.keys()), n=1, cutoff=0.55)

# #     if matches:
# #         return candidates[matches[0]]

# #     return None






# # # ---------------------------------------------------------
# # # Retriever
# # # ---------------------------------------------------------

# # def get_retriever():
# #     vectorstore = get_vectorstore()

# #     return vectorstore.as_retriever(
# #         search_type="similarity_score_threshold",
# #         search_kwargs={
# #             "k": TOP_K,
# #             "score_threshold": 0.85,
# #         },
# #     )


# # # ---------------------------------------------------------
# # # Search
# # # ---------------------------------------------------------

# # def similarity_search(query, k=None):
# #     matched = match_document(query)

# #     if matched is None:
# #         return []

# #     vectorstore = get_vectorstore()

# #     if k is None:
# #         k = TOP_K

# #     docs = vectorstore.similarity_search(matched, k=k)

# #     valid_docs = []

# #     for doc in docs:

# #         stored_name = (
# #             doc.metadata.get("document_name", "").lower().strip()
# #         )

# #         if stored_name == matched:
# #             valid_docs.append(doc)

# #     return valid_docs


# # # ---------------------------------------------------------
# # # Context
# # # ---------------------------------------------------------

# # def documents_to_context(documents):

# #     if not documents:
# #         return ""

# #     parts = []

# #     for doc in documents:

# #         parts.append(
# #             f"Template ID: {doc.metadata.get('template_id','unknown')}\n"
# #             f"Document Name: {doc.metadata.get('document_name','unknown')}\n\n"
# #             f"{doc.page_content}"
# #         )

# #     return "\n\n".join(parts)










# from pathlib import Path
# import re
# import numpy as np

# from langchain_huggingface import HuggingFaceEmbeddings
# from langchain_chroma import Chroma
# from langchain_core.documents import Document
# from langchain_text_splitters import RecursiveCharacterTextSplitter

# from config.config import (
#     EMBEDDING_MODEL,
#     CHROMA_PATH,
#     COLLECTION_NAME,
#     CHUNK_SIZE,
#     CHUNK_OVERLAP,
#     TOP_K
# )

# from metadata.metadata import get_all_templates

# # ---------------------------------------------------------
# # Embeddings
# # ---------------------------------------------------------

# _embeddings = None


# def get_embeddings():
#     global _embeddings

#     if _embeddings is None:
#         _embeddings = HuggingFaceEmbeddings(
#             model_name=EMBEDDING_MODEL,
#             model_kwargs={"device": "cpu"},
#             encode_kwargs={"normalize_embeddings": True}
#         )

#     return _embeddings


# # ---------------------------------------------------------
# # Text Splitter
# # ---------------------------------------------------------

# def get_text_splitter():
#     return RecursiveCharacterTextSplitter(
#         chunk_size=CHUNK_SIZE,
#         chunk_overlap=CHUNK_OVERLAP,
#         separators=["\n\n", "\n", ". ", " ", ""]
#     )


# # ---------------------------------------------------------
# # Chroma
# # ---------------------------------------------------------

# def get_vectorstore():
#     return Chroma(
#         collection_name=COLLECTION_NAME,
#         persist_directory=str(CHROMA_PATH),
#         embedding_function=get_embeddings()
#     )


# # ---------------------------------------------------------
# # Create Documents
# # ---------------------------------------------------------

# def create_documents(texts, metadatas=None):
#     docs = []

#     for i, text in enumerate(texts):

#         metadata = {}

#         if metadatas and i < len(metadatas):
#             metadata = metadatas[i]

#         docs.append(Document(page_content=text, metadata=metadata))

#     return docs


# # ---------------------------------------------------------
# # Split Documents
# # ---------------------------------------------------------

# def split_documents(documents):
#     return get_text_splitter().split_documents(documents)


# # ---------------------------------------------------------
# # Add Documents
# # ---------------------------------------------------------

# def add_documents(documents):
#     vectorstore = get_vectorstore()
#     vectorstore.add_documents(documents)
#     return vectorstore


# # # ---------------------------------------------------------
# # # Normalize User Query
# # # ---------------------------------------------------------

# # STOP_WORDS = {
# #     "i", "need", "want", "please", "give", "generate", "create",
# #     "make", "me", "a", "an", "the", "get", "show", "find",
# #     "template", "document", "form"
# # }


# # def _normalize(text):
# #     text = text.lower()

# #     text = re.sub(r"[^a-z0-9 ]", " ", text)

# #     words = [
# #         word for word in text.split()
# #         if word not in STOP_WORDS
# #     ]

# #     return " ".join(words)


# # # ---------------------------------------------------------
# # # Match Requested Document
# # # ---------------------------------------------------------

# # def match_document(query):
# #     query = _normalize(query)

# #     if not query:
# #         return None

# #     templates = get_all_templates()

# #     candidates = {}

# #     for template in templates:

# #         name = template.get("document_name", "").lower().strip()

# #         if name:
# #             candidates[name] = name

# #     # --------------------------------------------
# #     # Exact phrase
# #     # --------------------------------------------

# #     if query in candidates:
# #         return candidates[query]

# #     # --------------------------------------------
# #     # Substring
# #     # --------------------------------------------

# #     for phrase, actual in candidates.items():

# #         if query in phrase or phrase in query:
# #             return actual

# #     # --------------------------------------------
# #     # Keyword overlap
# #     # --------------------------------------------

# #     query_words = set(query.split())

# #     best_match = None
# #     best_score = 0

# #     for phrase, actual in candidates.items():

# #         phrase_words = set(phrase.split())

# #         overlap = len(query_words & phrase_words)

# #         score = overlap / max(len(phrase_words), 1)

# #         if score > best_score:
# #             best_score = score
# #             best_match = actual

# #     # Example:
# #     # leave agreement
# #     # -> leave and license agreement
# #     if best_score >= 0.5:
# #         return best_match

# #     # --------------------------------------------
# #     # Fuzzy fallback
# #     # --------------------------------------------

# #     matches = get_close_matches(
# #         query,
# #         list(candidates.keys()),
# #         n=1,
# #         cutoff=0.60
# #     )

# #     if matches:
# #         return candidates[matches[0]]

# #     return None


# # # ---------------------------------------------------------
# # # Retriever
# # # ---------------------------------------------------------

# # def get_retriever():
# #     vectorstore = get_vectorstore()

# #     return vectorstore.as_retriever(
# #         search_type="similarity_score_threshold",
# #         search_kwargs={
# #             "k": TOP_K,
# #             "score_threshold": 0.85
# #         }
# #     )




# # ---------------------------------------------------------
# # Semantic Document Intent Matching
# # ---------------------------------------------------------

# STOP_WORDS = {
#     "i", "need", "want", "please", "give", "generate",
#     "create", "make", "show", "find", "get", "me",
#     "a", "an", "the", "template", "document", "form"
# }


# def _normalize(text):
#     text = text.lower()
#     text = re.sub(r"[^a-z0-9 ]", " ", text)

#     words = [
#         word for word in text.split()
#         if word not in STOP_WORDS
#     ]

#     return " ".join(words)


# # Cache template embeddings
# _template_cache = None


# def get_template_embeddings():
#     """
#     Build embeddings for document names once.
#     """

#     global _template_cache

#     if _template_cache is not None:
#         return _template_cache

#     templates = get_all_templates()
#     embedding_model = get_embeddings()

#     names = []
#     vectors = []

#     for template in templates:

#         name = template.get("document_name")

#         if not name:
#             continue

#         normalized_name = _normalize(name)

#         names.append(normalized_name)
#         vectors.append(
#             embedding_model.embed_query(normalized_name)
#         )

#     _template_cache = (
#         names,
#         np.array(vectors)
#     )

#     return _template_cache


# def match_document(query):
#     """
#     Find the intended document using semantic similarity.
#     """

#     query = _normalize(query)

#     if not query:
#         return None

#     names, vectors = get_template_embeddings()

#     query_vector = np.array(
#         get_embeddings().embed_query(query)
#     )

#     # Embeddings are already normalized,
#     # so dot product equals cosine similarity.
#     scores = np.dot(vectors, query_vector)

#     best_index = int(np.argmax(scores))
#     best_score = float(scores[best_index])

#     print(
#         f"[Intent Match] '{query}' "
#         f"→ '{names[best_index]}' "
#         f"(score={best_score:.3f})"
#     )

#     # Confidence threshold
#     if best_score >= 0.70:
#         return names[best_index]

#     return None

# # ---------------------------------------------------------
# # Search
# # ---------------------------------------------------------

# def similarity_search(query, k=None):

#     matched = match_document(query)

#     if matched is None:
#         return []

#     vectorstore = get_vectorstore()

#     if k is None:
#         k = TOP_K

#     docs = vectorstore.similarity_search(matched, k=k)

#     valid_docs = []

#     for doc in docs:

#         stored_name = doc.metadata.get(
#             "document_name",
#             ""
#         ).lower().strip()

#         if _normalize(stored_name) == matched:
#             valid_docs.append(doc)

#     return valid_docs


# # ---------------------------------------------------------
# # Context
# # ---------------------------------------------------------

# def documents_to_context(documents):

#     if not documents:
#         return ""

#     parts = []

#     for doc in documents:

#         parts.append(
#             f"Template ID: {doc.metadata.get('template_id','unknown')}\n"
#             f"Document Name: {doc.metadata.get('document_name','unknown')}\n\n"
#             f"{doc.page_content}"
#         )

#     return "\n\n".join(parts)






















# from langchain_huggingface import HuggingFaceEmbeddings
# from langchain_chroma import Chroma
# from langchain_core.documents import Document
# from langchain_text_splitters import RecursiveCharacterTextSplitter

# from config.config import (
#     EMBEDDING_MODEL,
#     CHROMA_PATH,
#     COLLECTION_NAME,
#     CHUNK_SIZE,
#     CHUNK_OVERLAP,
#     TOP_K,
# )

# # ==========================================================
# # Embedding Model (Singleton)
# # ==========================================================

# _embeddings = None


# def get_embeddings():
#     global _embeddings

#     if _embeddings is None:
#         _embeddings = HuggingFaceEmbeddings(
#             model_name=EMBEDDING_MODEL,
#             model_kwargs={"device": "cpu"},
#             encode_kwargs={"normalize_embeddings": True},
#         )

#     return _embeddings


# # ==========================================================
# # Text Splitter
# # ==========================================================

# def get_text_splitter():
#     return RecursiveCharacterTextSplitter(
#         chunk_size=CHUNK_SIZE,
#         chunk_overlap=CHUNK_OVERLAP,
#         separators=["\n\n", "\n", ". ", " ", ""],
#     )


# # ==========================================================
# # Chroma Vector Store
# # ==========================================================

# def get_vectorstore():
#     return Chroma(
#         collection_name=COLLECTION_NAME,
#         persist_directory=str(CHROMA_PATH),
#         embedding_function=get_embeddings(),
#     )


# # ==========================================================
# # Create LangChain Documents
# # ==========================================================

# def create_documents(texts, metadatas=None):
#     docs = []

#     for index, text in enumerate(texts):
#         metadata = {}

#         if metadatas and index < len(metadatas):
#             metadata = metadatas[index]

#         docs.append(
#             Document(
#                 page_content=text,
#                 metadata=metadata,
#             )
#         )

#     return docs


# # ==========================================================
# # Split Documents
# # ==========================================================

# def split_documents(documents):
#     splitter = get_text_splitter()
#     return splitter.split_documents(documents)


# # ==========================================================
# # Add Documents
# # ==========================================================

# def add_documents(documents):
#     vectorstore = get_vectorstore()
#     vectorstore.add_documents(documents)
#     return vectorstore


# # ==========================================================
# # LangChain Retriever
# # ==========================================================

# def get_retriever():
#     vectorstore = get_vectorstore()

#     return vectorstore.as_retriever(
#         search_type="similarity_score_threshold",
#         search_kwargs={
#             "k": TOP_K,
#             "score_threshold": 0.70,
#         },
#     )


# # ==========================================================
# # Retrieve Documents
# # ==========================================================

# # def retrieve_documents(query):
# #     retriever = get_retriever()
# #     return retriever.invoke(query)
# # ==========================================================
# # Retrieve Documents (Semantic RAG)
# # ==========================================================

# def retrieve_documents(query):
#     vectorstore = get_vectorstore()

#     results = vectorstore.similarity_search_with_relevance_scores(
#         query,
#         k=TOP_K
#     )

#     if not results:
#         return []

#     for doc, score in results:
#         print(f"[RAG] {doc.metadata.get('document_name')} -> {score:.3f}")

#     best_doc, best_score = results[0];

#     if best_score >=0.45:
#         return [best_doc]

#     return[]

# # ==========================================================
# # Convert Retrieved Docs to Context
# # ==========================================================

# def documents_to_context(documents):
#     if not documents:
#         return ""

#     context_parts = []

#     for document in documents:
#         context_parts.append(
#             f"Template ID: {document.metadata.get('template_id', 'unknown')}\n"
#             f"Document Name: {document.metadata.get('document_name', 'unknown')}\n"
#             f"Document Type: {document.metadata.get('document_type', 'unknown')}\n\n"
#             f"{document.page_content}"
#         )

#     return "\n\n".join(context_parts)















# from difflib import get_close_matches
# import re
# import numpy as np
# from rapidfuzz import process, fuzz
# from metadata.metadata import get_all_templates

# from langchain_huggingface import HuggingFaceEmbeddings
# from langchain_chroma import Chroma
# from langchain_core.documents import Document
# from langchain_text_splitters import RecursiveCharacterTextSplitter

# from config.config import (
#     EMBEDDING_MODEL,
#     CHROMA_PATH,
#     COLLECTION_NAME,
#     CHUNK_SIZE,
#     CHUNK_OVERLAP,
#     TOP_K,
# )

# from metadata.metadata import get_all_templates

# # ==========================================================
# # Embedding Model (Singleton)
# # ==========================================================

# _embeddings = None


# def get_embeddings():
#     global _embeddings

#     if _embeddings is None:
#         _embeddings = HuggingFaceEmbeddings(
#             model_name=EMBEDDING_MODEL,
#             model_kwargs={"device": "cpu"},
#             encode_kwargs={"normalize_embeddings": True},
#         )

#     return _embeddings


# # ==========================================================
# # Text Splitter
# # ==========================================================

# def get_text_splitter():
#     return RecursiveCharacterTextSplitter(
#         chunk_size=CHUNK_SIZE,
#         chunk_overlap=CHUNK_OVERLAP,
#         separators=["\n\n", "\n", ". ", " ", ""],
#     )


# # ==========================================================
# # Chroma Vector Store
# # ==========================================================

# def get_vectorstore():
#     return Chroma(
#         collection_name=COLLECTION_NAME,
#         persist_directory=str(CHROMA_PATH),
#         embedding_function=get_embeddings(),
#     )


# # ==========================================================
# # Create LangChain Documents
# # ==========================================================

# def create_documents(texts, metadatas=None):

#     documents = []

#     for index, text in enumerate(texts):

#         metadata = {}

#         if metadatas and index < len(metadatas):
#             metadata = metadatas[index]

#         documents.append(
#             Document(
#                 page_content=text,
#                 metadata=metadata,
#             )
#         )

#     return documents


# # ==========================================================
# # Split Documents
# # ==========================================================

# def split_documents(documents):
#     splitter = get_text_splitter()
#     return splitter.split_documents(documents)


# # ==========================================================
# # Add Documents
# # ==========================================================

# def add_documents(documents):
#     vectorstore = get_vectorstore()
#     vectorstore.add_documents(documents)
#     return vectorstore


# # ==========================================================
# # LangChain Retriever
# # ==========================================================

# def get_retriever():
#     vectorstore = get_vectorstore()

#     return vectorstore.as_retriever(
#         search_type="similarity",
#         search_kwargs={"k": TOP_K},
#     )


# # ==========================================================
# # Build Template Name Embeddings
# # ==========================================================

# _template_cache = None


# def get_template_name_embeddings():
#     """
#     Build embeddings for all document names once.
#     """

#     global _template_cache

#     if _template_cache is not None:
#         return _template_cache

#     embedding_model = get_embeddings()

#     names = []
#     vectors = []

#     for template in get_all_templates():

#         name = template.get("document_name")

#         if not name:
#             continue

#         names.append(name)
#         vectors.append(
#             embedding_model.embed_query(name.lower())
#         )

#     _template_cache = (
#         names,
#         np.array(vectors),
#     )

#     return _template_cache

# # ==========================================================
# # Query Normalization + Spell Correction
# # ==========================================================

# STOP_WORDS = {
#     "i", "need", "want", "please", "give", "provide", "fetch",
#     "show", "get", "me", "a", "an", "the", "template",
#     "document", "format", "file", "for"
# }

# def normalize_query(query):
#     query = query.lower()
#     query = re.sub(r"[^a-z0-9 ]", " ", query)
#     query = re.sub(r"\s+", " ", query).strip()
#     return query


# def correct_query(query):
#     """
#     Correct spelling using words that already exist
#     in document names from the knowledge base.
#     """

#     query = normalize_query(query)

#     templates = get_all_templates()

#     vocabulary = set()

#     for template in templates:
#         name = template.get("document_name", "").lower()
#         vocabulary.update(name.split())

#     corrected_words = []

#     for word in query.split():

#         if word in STOP_WORDS:
#             continue

#         if word in vocabulary:
#             corrected_words.append(word)
#             continue

#         match = get_close_matches(word, list(vocabulary), n=1, cutoff=0.75)

#         if match:
#             corrected_words.append(match[0])
#         else:
#             corrected_words.append(word)

#     corrected_query = " ".join(corrected_words)

#     print(f"[Query] '{query}' -> '{corrected_query}'")

#     return corrected_query

# # ==========================================================
# # Retrieve Documents (Semantic RAG)
# # ==========================================================

# def retrieve_documents(query):

#     query = correct_query(query)

#     retriever = get_retriever()
#     retrieved_docs = retriever.invoke(query)

#     if not retrieved_docs:
#         return []

#     names, vectors = get_template_name_embeddings()

#     query_vector = np.array(
#         get_embeddings().embed_query(query.lower())
#     )

#     # cosine similarity (embeddings already normalized)
#     scores = np.dot(vectors, query_vector)

#     best_index = int(np.argmax(scores))
#     best_score = float(scores[best_index])

#     best_name = names[best_index].lower()

#     print(
#         f"[Intent Match] '{query}' → '{best_name}' "
#         f"(score={best_score:.3f})"
#     )

#     # Reject unrelated queries
#     if best_score < 0.60:
#         return []

#     # Return only retrieved chunks belonging
#     # to the matched document
#     filtered = []

#     for doc in retrieved_docs:

#         stored_name = (
#             doc.metadata.get("document_name", "")
#             .lower()
#             .strip()
#         )

#         if stored_name == best_name:
#             filtered.append(doc)

#     return filtered


# # ==========================================================
# # Convert Retrieved Documents to Context
# # ==========================================================

# def documents_to_context(documents):

#     if not documents:
#         return ""

#     context_parts = []

#     for document in documents:

#         context_parts.append(
#             f"Template ID: {document.metadata.get('template_id', 'unknown')}\n"
#             f"Document Name: {document.metadata.get('document_name', 'unknown')}\n"
#             f"Document Type: {document.metadata.get('document_type', 'unknown')}\n\n"
#             f"{document.page_content}"
#         )

#     return "\n\n".join(context_parts)


















import re
from rapidfuzz import process, fuzz

from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

from config.config import (
    EMBEDDING_MODEL,
    CHROMA_PATH,
    COLLECTION_NAME,
    CHUNK_SIZE,
    CHUNK_OVERLAP,
    TOP_K,
)

from metadata.metadata import get_all_templates

# ==========================================================
# Embedding Model (Singleton)
# ==========================================================

_embeddings = None
def get_embeddings():
    global _embeddings
    if _embeddings is None:
        _embeddings = HuggingFaceEmbeddings(
            model_name=EMBEDDING_MODEL,
            model_kwargs={"device": "cpu"},
            encode_kwargs={"normalize_embeddings": True},
        )
    return _embeddings
# ==========================================================
# Text Splitter
# ==========================================================
def get_text_splitter():
    return RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        separators=["\n\n", "\n", ". ", " ", ""],
    )
# ==========================================================
# Chroma Vector Store
# ==========================================================
def get_vectorstore():
    return Chroma(
        collection_name=COLLECTION_NAME,
        persist_directory=str(CHROMA_PATH),
        embedding_function=get_embeddings(),
    )
# ==========================================================
# Create LangChain Documents
# ==========================================================
def create_documents(texts, metadatas=None):
    docs = []
    for index, text in enumerate(texts):
        metadata = {}
        if metadatas and index < len(metadatas):
            metadata = metadatas[index]
        docs.append(Document(page_content=text,metadata=metadata,))
    return docs
# ==========================================================
# Split Documents
# ==========================================================
def split_documents(documents):
    splitter = get_text_splitter()
    return splitter.split_documents(documents)
# ==========================================================
# Add Documents
# ==========================================================
def add_documents(documents):
    vectorstore = get_vectorstore()
    vectorstore.add_documents(documents)
    return vectorstore
# ==========================================================
# LangChain Retriever
# ==========================================================
def get_retriever():
    vectorstore = get_vectorstore()
    return vectorstore.as_retriever(
        search_type="similarity_score_threshold",
        search_kwargs={
            "k": TOP_K,
            "score_threshold": 0.70,
        },
    )
# ==========================================================
# Query Processing
# ==========================================================

STOP_WORDS = {
    "i", "need", "want", "please", "give", "provide",
    "fetch", "show", "get", "me", "a", "an",
    "the", "template", "document", "format",
    "file", "for", "of", "my"
}

_cache = None

# ----------------------------------------------------------
# Hindi / Hinglish Alias Map
# ----------------------------------------------------------

HINDI_ALIAS_MAP = {

    # Affidavit
    "शपथ पत्र": "affidavit",
    "शपथपत्र": "affidavit",
    "हलफनामा": "affidavit",
    "एफिडेविट": "affidavit",
    "halafnama": "affidavit",
    "shapath patra": "affidavit",
    "sapath patra": "affidavit",

    # Certificate of Taxation
    "कराधान प्रमाणपत्र": "certificate of taxation",
    "टैक्स प्रमाणपत्र": "certificate of taxation",

    # General Legal Notice
    "कानूनी नोटिस": "general legal notice",
    "लीगल नोटिस": "general legal notice",
    "vakil notice": "general legal notice",

    # Leave & License
    "लीव एंड लाइसेंस एग्रीमेंट": "leave and license agreement",
    "लीव लाइसेंस समझौता": "leave and license agreement",

    # Non Payment
    "बकाया भुगतान नोटिस": "legal notice for non payment of dues",
    "भुगतान वसूली नोटिस": "legal notice for non payment of dues",

    # Rent Agreement
    "किराया समझौता": "rent agreement",
    "रेंट एग्रीमेंट": "rent agreement",
    "kiraya samjhauta": "rent agreement",

    # Writ of Commission
    "आयोग रिट": "writ of commission",
    "गवाह जांच आयोग": "writ of commission"
}


def normalize_multilingual_query(query):
    """
    Normalize Hindi, Roman Hindi, and common STT spelling variations
    into canonical English document names.
    """

    q = query.lower()

    alias_groups = {
        "affidavit": [
            "शपथ पत्र", "शपथपत्र", "शपत पत्र",
            "हलफनामा",
            "एफिडेविट", "एफेडेविट", "एफिडविट",
            "halafnama", "shapath patra", "sapath patra"
        ],

        "rent agreement": [
            "रेंट एग्रीमेंट", "रेंट एग्रिमेंट",
            "किराया समझौता",
            "kiraya samjhauta"
        ],

        "leave and license agreement": [
            "लीव एंड लाइसेंस एग्रीमेंट",
            "लीव लाइसेंस समझौता"
        ],

        "general legal notice": [
            "कानूनी नोटिस",
            "लीगल नोटिस",
            "vakil notice"
        ],

        "legal notice for non payment of dues": [
            "बकाया भुगतान नोटिस",
            "भुगतान वसूली नोटिस"
        ],

        "certificate of taxation": [
            "टैक्स प्रमाणपत्र",
            "कराधान प्रमाणपत्र",
            "टेक्स प्रमाणपत्र"
        ],

        "writ of commission": [
            "आयोग रिट",
            "कमीशन रिट",
            "गवाह जांच आयोग"
        ]
    }

    # Exact replacement first
    for canonical, aliases in alias_groups.items():
        for alias in aliases:
            if alias.lower() in q:
                q = q.replace(alias.lower(), canonical)

    # Fuzzy fallback for Hindi phrases
    for canonical, aliases in alias_groups.items():
        for alias in aliases:
            if any('\u0900' <= ch <= '\u097F' for ch in alias):
                if fuzz.partial_ratio(q, alias.lower()) >= 85:
                    return canonical

    return q

def build_vocabulary():
    """
    Build vocabulary from document names
    and aliases.
    """

    global _cache

    if _cache is not None:
        return _cache

    templates = get_all_templates()

    vocabulary = set()

    for template in templates:

        name = template.get("document_name", "").lower()

        for word in re.findall(r"[a-z]+", name):
            vocabulary.add(word)

        for alias in template.get("aliases", []):

            alias = alias.lower()

            for word in re.findall(r"[a-z]+", alias):
                vocabulary.add(word)

    _cache = sorted(vocabulary)

    return _cache
def correct_query(query):
    """
    Spell correction while preserving Hindi text.
    """

    vocabulary = build_vocabulary()

    query = normalize_multilingual_query(query)

    original_query = query

    query = re.sub(r"[^\w\u0900-\u097F ]", " ", query)

    query = re.sub(r"\s+", " ", query).strip()

    corrected = []

    for word in query.split():

        if re.search(r"[\u0900-\u097F]", word):
            corrected.append(word)
            continue

        if word in STOP_WORDS:
            corrected.append(word)
            continue

        if word in vocabulary:
            corrected.append(word)
            continue

        match = process.extractOne(
            word,
            vocabulary,
            scorer=fuzz.ratio,
            score_cutoff=72,
        )

        corrected.append(match[0] if match else word)

    corrected_query = " ".join(corrected)

    print(f"[QUERY] {original_query} -> {corrected_query}")

    return corrected_query
# ==========================================================
# Retrieve Documents (Semantic RAG)
# ==========================================================

# def retrieve_documents(query):

#     query = correct_query(query)

#     vectorstore = get_vectorstore()

#     results = vectorstore.similarity_search_with_relevance_scores(
#         query,
#         k=TOP_K,
#     )

#     if not results:
#         return []

#     for doc, score in results:
#         print(f"[RAG] {doc.metadata.get('document_name')} -> {score:.3f}")

#     best_doc, best_score = results[0]

#     if best_score >= 0.42:
#         return [best_doc]

#     return []
def retrieve_documents(query):
    """
    Retrieve the most relevant legal document
    using multilingual semantic search.
    """

    query = correct_query(query)

    vectorstore = get_vectorstore()

    results = vectorstore.similarity_search_with_relevance_scores(
        query,
        k=TOP_K,
    )

    if not results:
        return []

    for doc, score in results:
        print(f"[RAG] {doc.metadata.get('document_name')} -> {score:.3f}")

    q = query.lower()

    # ------------------------------------
    # Exact document name or alias match
    # ------------------------------------

    for doc, score in results:

        name = doc.metadata.get(
            "document_name",
            ""
        ).lower()

        aliases = [
            alias.lower()
            for alias in doc.metadata.get(
                "aliases",
                []
            )
        ]

        if name in q or q in name:
            return [doc]

        for alias in aliases:

            if alias in q or q in alias:
                return [doc]

    # ------------------------------------
    # Semantic fallback
    # ------------------------------------

    best_doc, best_score = results[0]

    if best_score >= 0.42:
        return [best_doc]

    return []
# ==========================================================
# Convert Retrieved Docs to Context
# ==========================================================

def documents_to_context(documents):
    if not documents:
        return ""
    context_parts = []
    for document in documents:
        context_parts.append(
            f"Template ID: {document.metadata.get('template_id', 'unknown')}\n"
            f"Document Name: {document.metadata.get('document_name', 'unknown')}\n"
            f"Document Type: {document.metadata.get('document_type', 'unknown')}\n\n"
            f"{document.page_content}"
        )
    return "\n\n".join(context_parts)