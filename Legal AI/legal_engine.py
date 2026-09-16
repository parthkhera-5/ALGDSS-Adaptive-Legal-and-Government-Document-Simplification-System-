# import json

# from groq import Groq

# from config import Config

# from retrieval import Retriever
# from context_selector import ContextSelector
# from knowledge_retrieval import KnowledgeRetriever

# from prompts import (
#     SYSTEM_PROMPT,
#     ROUTER_SYSTEM_PROMPT,
#     build_user_prompt,
#     build_router_prompt
# )


# class LegalEngine:

#     def __init__(self):

#         # ==================================================
#         # GROQ
#         # ==================================================

#         api_key = Config.GROQ_API_KEY

#         if not api_key:

#             raise ValueError(
#                 "GROQ_API_KEY is not configured."
#             )

#         self.client = Groq(
#             api_key=api_key
#         )

#         # ==================================================
#         # DOCUMENT RAG
#         # ==================================================

#         self.retriever = Retriever()

#         self.selector = ContextSelector()

#         # ==================================================
#         # KNOWLEDGE RAG
#         # ==================================================

#         print(
#             "\nInitializing legal knowledge RAG..."
#         )

#         self.knowledge_retriever = (
#             KnowledgeRetriever()
#         )

#         self.knowledge_retriever.initialize()

#         # ==================================================
#         # DOCUMENT STATE
#         # ==================================================

#         self.loaded = False

#         # ==================================================
#         # CONVERSATION MEMORY
#         # ==================================================

#         self.conversation_history = []

#         self.max_history = 6

#     # ======================================================
#     # BUILD CONVERSATION CONTEXT
#     # ======================================================

#     def build_conversation_context(self):

#         if not self.conversation_history:

#             return ""

#         history = []

#         for item in (
#             self.conversation_history[
#                 -self.max_history:
#             ]
#         ):

#             history.append(
#                 f"""
# USER:
# {item["query"]}

# ASSISTANT:
# {item["answer"]}
# """.strip()
#             )

#         return "\n\n---\n\n".join(
#             history
#         )

#     # ======================================================
#     # SAVE CONVERSATION
#     # ======================================================

#     def save_conversation(
#         self,
#         query,
#         answer
#     ):

#         self.conversation_history.append({

#             "query":
#                 query,

#             "answer":
#                 answer

#         })

#         self.conversation_history = (
#             self.conversation_history[
#                 -self.max_history:
#             ]
#         )

#     # ======================================================
#     # DOCUMENT INGESTION
#     # ======================================================

#     def load_document(
#         self,
#         records
#     ):

#         if not records:

#             raise ValueError(
#                 "No document records were found."
#             )

#         chunks = (
#             self.retriever.create_chunks(
#                 records
#             )
#         )

#         if not chunks:

#             raise ValueError(
#                 "No chunks could be created "
#                 "from the document."
#             )

#         self.retriever.build_index(
#             chunks
#         )

#         self.loaded = True

#         # --------------------------------------------------
#         # Clear previous conversation when a new document
#         # is uploaded.
#         # --------------------------------------------------

#         self.conversation_history = []

#         print(
#             "\nDocument successfully loaded."
#         )

#     # ======================================================
#     # BUILD DOCUMENT CONTEXT
#     # ======================================================

#     def build_context(
#         self,
#         selected_results
#     ):

#         if not selected_results:

#             return ""

#         ordered_results = sorted(
#             selected_results,
#             key=lambda x: (
#                 x.get(
#                     "source",
#                     ""
#                 ),
#                 x.get(
#                     "page",
#                     0
#                 ),
#                 x.get(
#                     "page_chunk_position",
#                     0
#                 ),
#                 x.get(
#                     "chunk_id",
#                     0
#                 )
#             )
#         )

#         context_parts = []

#         for position, result in enumerate(
#             ordered_results,
#             start=1
#         ):

#             source = result.get(
#                 "source",
#                 "Unknown"
#             )

#             page = result.get(
#                 "page",
#                 "Unknown"
#             )

#             chunk_id = result.get(
#                 "chunk_id",
#                 "Unknown"
#             )

#             text = result.get(
#                 "text",
#                 ""
#             ).strip()

#             if not text:

#                 continue

#             context_parts.append(
#                 f"""
# [CONTEXT {position}]
# Source: {source}
# Page: {page}
# Chunk ID: {chunk_id}

# {text}
# """.strip()
#             )

#         return "\n\n---\n\n".join(
#             context_parts
#         )

#     # ======================================================
#     # BUILD DOCUMENT SOURCES
#     # ======================================================

#     def build_sources(
#         self,
#         selected_results
#     ):

#         sources = []

#         seen = set()

#         for result in selected_results:

#             source = result.get(
#                 "source"
#             )

#             page = result.get(
#                 "page"
#             )

#             chunk_id = result.get(
#                 "chunk_id"
#             )

#             if source is None:

#                 continue

#             source_key = (
#                 source,
#                 page,
#                 chunk_id
#             )

#             if source_key in seen:

#                 continue

#             seen.add(
#                 source_key
#             )

#             sources.append({

#                 "source":
#                     source,

#                 "page":
#                     page,

#                 "chunk_id":
#                     chunk_id

#             })

#         return sources

#     # ======================================================
#     # BUILD KNOWLEDGE CONTEXT
#     # ======================================================

#     def build_knowledge_context(
#         self,
#         knowledge_results
#     ):

#         if not knowledge_results:

#             return ""

#         context_parts = []

#         for position, result in enumerate(
#             knowledge_results,
#             start=1
#         ):

#             question = result.get(
#                 "question",
#                 ""
#             )

#             answer = result.get(
#                 "answer",
#                 ""
#             )

#             source = result.get(
#                 "source",
#                 "unknown"
#             )

#             score = result.get(
#                 "score"
#             )

#             context_parts.append(
#                 f"""
# [KNOWLEDGE {position}]

# Source: {source}
# Relevance Score: {score}

# Question:
# {question}

# Answer:
# {answer}
# """.strip()
#             )

#         return "\n\n---\n\n".join(
#             context_parts
#         )

#     # ======================================================
#     # BUILD KNOWLEDGE SOURCES
#     # ======================================================

#     def build_knowledge_sources(
#         self,
#         knowledge_results
#     ):

#         sources = []

#         seen = set()

#         for result in knowledge_results:

#             knowledge_id = result.get(
#                 "knowledge_id"
#             )

#             source = result.get(
#                 "source",
#                 "unknown"
#             )

#             if knowledge_id is not None:

#                 source_key = (
#                     knowledge_id,
#                     source
#                 )

#             else:

#                 source_key = (
#                     result.get(
#                         "question",
#                         ""
#                     ),
#                     source
#                 )

#             if source_key in seen:

#                 continue

#             seen.add(
#                 source_key
#             )

#             sources.append({

#                 "knowledge_id":
#                     knowledge_id,

#                 "source":
#                     source,

#                 "question":
#                     result.get(
#                         "question",
#                         ""
#                     ),

#                 "score":
#                     result.get(
#                         "score"
#                     )

#             })

#         return sources

#     # ======================================================
#     # PARSE STRUCTURED LLM RESPONSE
#     # ======================================================

#     def parse_llm_response(
#         self,
#         raw_response
#     ):

#         if not raw_response:

#             return {

#                 "type":
#                     "response",

#                 "content": [

#                     {
#                         "type":
#                             "paragraph",

#                         "text":
#                             "No answer was generated."
#                     }

#                 ]

#             }

#         raw_response = raw_response.strip()

#         # --------------------------------------------------
#         # Remove markdown code fences
#         # --------------------------------------------------

#         if raw_response.startswith(
#             "```json"
#         ):

#             raw_response = raw_response[
#                 len("```json"):
#             ].strip()

#         elif raw_response.startswith(
#             "```"
#         ):

#             raw_response = raw_response[
#                 len("```"):
#             ].strip()

#         if raw_response.endswith(
#             "```"
#         ):

#             raw_response = raw_response[
#                 :-3
#             ].strip()

#         # --------------------------------------------------
#         # Parse JSON
#         # --------------------------------------------------

#         try:

#             parsed = json.loads(
#                 raw_response
#             )

#             if not isinstance(
#                 parsed,
#                 dict
#             ):

#                 raise ValueError(
#                     "LLM response is not "
#                     "a JSON object."
#                 )

#             answer_type = parsed.get(
#                 "type",
#                 "mixed"
#             )

#             content = parsed.get(
#                 "content",
#                 []
#             )

#             if answer_type not in {
#                 "mixed",
#                 "response"
#             }:

#                 answer_type = "mixed"

#             if (
#                 not isinstance(
#                     content,
#                     list
#                 )
#                 or not content
#             ):

#                 raise ValueError(
#                     "Invalid or empty content."
#                 )

#             return {

#                 "type":
#                     answer_type,

#                 "content":
#                     content

#             }

#         except (
#             json.JSONDecodeError,
#             ValueError
#         ):

#             print(
#                 "\nWarning: "
#                 "LLM returned invalid JSON."
#             )

#             print(
#                 "Raw response:"
#             )

#             print(
#                 raw_response
#             )

#             return {

#                 "type":
#                     "response",

#                 "content": [

#                     {
#                         "type":
#                             "paragraph",

#                         "text":
#                             raw_response
#                     }

#                 ]

#             }

#     # ======================================================
#     # CONVERT ANSWER TO TEXT
#     # ======================================================

#     def answer_to_text(
#         self,
#         answer
#     ):

#         if not isinstance(
#             answer,
#             dict
#         ):

#             return str(answer)

#         texts = []

#         for item in answer.get(
#             "content",
#             []
#         ):

#             item_type = item.get(
#                 "type"
#             )

#             if item_type in {
#                 "paragraph",
#                 "heading",
#                 "warning"
#             }:

#                 text = item.get(
#                     "text",
#                     ""
#                 )

#                 if text:

#                     texts.append(
#                         text
#                     )

#             elif item_type in {
#                 "bullet_list",
#                 "numbered_list"
#             }:

#                 items = item.get(
#                     "items",
#                     []
#                 )

#                 for text in items:

#                     if text:

#                         texts.append(
#                             f"- {text}"
#                         )

#         return "\n".join(
#             texts
#         )

#     # ======================================================
#     # DETERMINE ROUTE
#     # ======================================================

#     def determine_route(
#         self,
#         query,
#         operation
#     ):

#         conversation_context = (
#             self.build_conversation_context()
#         )

#         router_prompt = build_router_prompt(

#             query=query,

#             conversation_context=
#                 conversation_context,

#             document_loaded=
#                 self.loaded,

#             operation=
#                 operation
#         )

#         print(
#             "\n" + "=" * 80
#         )

#         print(
#             "LEGAL AI ROUTER"
#         )

#         print(
#             "=" * 80
#         )

#         try:

#             response = (
#                 self.client
#                 .chat
#                 .completions
#                 .create(

#                     model=
#                         Config.GROQ_MODEL,

#                     messages=[

#                         {
#                             "role":
#                                 "system",

#                             "content":
#                                 ROUTER_SYSTEM_PROMPT
#                         },

#                         {
#                             "role":
#                                 "user",

#                             "content":
#                                 router_prompt
#                         }

#                     ],

#                     temperature=0
#                 )
#             )

#             raw_route = (
#                 response
#                 .choices[0]
#                 .message
#                 .content
#                 .strip()
#             )

#             # --------------------------------------------------
#             # Remove code fences
#             # --------------------------------------------------

#             if raw_route.startswith(
#                 "```json"
#             ):

#                 raw_route = raw_route[
#                     len("```json"):
#                 ].strip()

#             elif raw_route.startswith(
#                 "```"
#             ):

#                 raw_route = raw_route[
#                     len("```"):
#                 ].strip()

#             if raw_route.endswith(
#                 "```"
#             ):

#                 raw_route = raw_route[
#                     :-3
#                 ].strip()

#             parsed = json.loads(
#                 raw_route
#             )

#             route = str(
#                 parsed.get(
#                     "route",
#                     "KNOWLEDGE"
#                 )
#             ).upper()

#             if route not in {
#                 "DOCUMENT",
#                 "KNOWLEDGE",
#                 "BOTH"
#             }:

#                 route = "KNOWLEDGE"

#             # --------------------------------------------------
#             # Operation-specific safety rules
#             # --------------------------------------------------

#             if operation == "SUMMARY":

#                 route = "DOCUMENT"

#             elif (
#                 operation == "CLAUSE_EXPLANATION"
#                 and self.loaded
#             ):

#                 route = "DOCUMENT"

#             elif (
#                 operation == "RISK_DETECTION"
#                 and self.loaded
#             ):

#                 route = "DOCUMENT"

#             elif (
#                 operation == "LEGAL_VALIDATION"
#                 and self.loaded
#             ):

#                 # Allow BOTH for legal validation.
#                 if route == "KNOWLEDGE":

#                     route = "BOTH"

#             # --------------------------------------------------
#             # Cannot use document if none is loaded
#             # --------------------------------------------------

#             if (
#                 route in {
#                     "DOCUMENT",
#                     "BOTH"
#                 }
#                 and not self.loaded
#             ):

#                 route = "KNOWLEDGE"

#             print(
#                 f"Selected route: {route}"
#             )

#             return route

#         except Exception as e:

#             print(
#                 f"\nRouting failed: {e}"
#             )

#             # --------------------------------------------------
#             # Safe fallback
#             # --------------------------------------------------

#             if (
#                 operation == "SUMMARY"
#                 and self.loaded
#             ):

#                 return "DOCUMENT"

#             if self.loaded:

#                 return "DOCUMENT"

#             return "KNOWLEDGE"

#     # ======================================================
#     # DOCUMENT RETRIEVAL
#     # ======================================================

#     def retrieve_document(
#         self,
#         query,
#         operation
#     ):

#         if not self.loaded:

#             return []

#         # --------------------------------------------------
#         # SUMMARY
#         # --------------------------------------------------

#         if operation == "SUMMARY":

#             print(
#                 "\nDocument summary:"
#                 " retrieving all chunks."
#             )

#             return (
#                 self.retriever
#                 .get_all_chunks()
#             )

#         # --------------------------------------------------
#         # Normal document retrieval
#         # --------------------------------------------------

#         results = (
#             self.retriever.search(
#                 query,
#                 include_neighbors=True
#             )
#         )

#         if not results:

#             return []

#         # --------------------------------------------------
#         # Reranking
#         # --------------------------------------------------

#         print(
#             "\nReranking document chunks..."
#         )

#         reranked_results = (
#             self.selector.rerank(
#                 query,
#                 results
#             )
#         )

#         # --------------------------------------------------
#         # Relevance gate
#         # --------------------------------------------------

#         if not self.selector.is_relevant(
#             reranked_results
#         ):

#             print(
#                 "Document retrieval:"
#                 " no sufficiently relevant chunks."
#             )

#             return []

#         # --------------------------------------------------
#         # Context selection
#         # --------------------------------------------------

#         selected_results = (
#             self.selector.select(
#                 reranked_results
#             )
#         )

#         return selected_results

#     # ======================================================
#     # KNOWLEDGE RETRIEVAL
#     # ======================================================

#     def retrieve_knowledge(
#         self,
#         query
#     ):

#         print(
#             "\nSearching legal knowledge base..."
#         )

#         results = (
#             self.knowledge_retriever.search(
#                 query,
#                 top_k=Config.KNOWLEDGE_TOP_K
#             )
#         )

#         print(
#             f"Knowledge results: {len(results)}"
#         )

#         for result in results:

#             print(
#                 f"\nKnowledge ID: "
#                 f"{result.get('knowledge_id')}"
#             )

#             print(
#                 f"Score: "
#                 f"{result.get('score')}"
#             )

#             print(
#                 f"Source: "
#                 f"{result.get('source')}"
#             )

#             print(
#                 f"Question: "
#                 f"{result.get('question')}"
#             )

#         return results

#     # ======================================================
#     # ASK QUESTION
#     # ======================================================

#     def ask(
#         self,
#         query,
#         operation="DOCUMENT_QA"
#     ):

#         # ==================================================
#         # QUERY CHECK
#         # ==================================================

#         if not query or not query.strip():

#             return {

#                 "answer":
#                     "Please enter a question.",

#                 "sources": []

#             }

#         query = query.strip()

#         # ==================================================
#         # VALID OPERATIONS
#         # ==================================================

#         allowed_operations = {

#             "DOCUMENT_QA",

#             "SUMMARY",

#             "CLAUSE_EXPLANATION",

#             "RISK_DETECTION",

#             "LEGAL_VALIDATION",

#             "GENERAL_LEGAL_QA"

#         }

#         if operation not in allowed_operations:

#             operation = "DOCUMENT_QA"

#         # ==================================================
#         # 1. ROUTING
#         # ==================================================

#         route = self.determine_route(
#             query,
#             operation
#         )

#         # ==================================================
#         # 2. DOCUMENT RETRIEVAL
#         # ==================================================

#         document_results = []

#         if route in {
#             "DOCUMENT",
#             "BOTH"
#         }:

#             document_results = (
#                 self.retrieve_document(
#                     query,
#                     operation
#                 )
#             )

#         # ==================================================
#         # 3. KNOWLEDGE RETRIEVAL
#         # ==================================================

#         knowledge_results = []

#         if route in {
#             "KNOWLEDGE",
#             "BOTH"
#         }:

#             knowledge_results = (
#                 self.retrieve_knowledge(
#                     query
#                 )
#             )

#         # ==================================================
#         # 4. BUILD CONTEXTS
#         # ==================================================

#         document_context = (
#             self.build_context(
#                 document_results
#             )
#         )

#         knowledge_context = (
#             self.build_knowledge_context(
#                 knowledge_results
#             )
#         )

#         # ==================================================
#         # 5. CHECK WHETHER ANY CONTEXT EXISTS
#         # ==================================================

#         if (
#             not document_context
#             and not knowledge_context
#         ):

#             if route == "DOCUMENT":

#                 message = (
#                     "I could not find sufficiently "
#                     "relevant information in the "
#                     "uploaded document."
#                 )

#             elif route == "KNOWLEDGE":

#                 message = (
#                     "I could not find relevant "
#                     "information in the legal "
#                     "knowledge base."
#                 )

#             else:

#                 message = (
#                     "I could not find sufficiently "
#                     "relevant information in the "
#                     "available sources."
#                 )

#             return {

#                 "answer": {

#                     "type":
#                         "response",

#                     "content": [

#                         {
#                             "type":
#                                 "paragraph",

#                             "text":
#                                 message
#                         }

#                     ]

#                 },

#                 "document_based":
#                     False,

#                 "knowledge_based":
#                     False,

#                 "route":
#                     route,

#                 "operation":
#                     operation,

#                 "sources":
#                     [],

#                 "knowledge_sources":
#                     [],

#                 "selected_chunks":
#                     []

#             }

#         # ==================================================
#         # 6. DEBUG CONTEXT
#         # ==================================================

#         if document_context:

#             print(
#                 "\n" + "=" * 80
#             )

#             print(
#                 "DOCUMENT CONTEXT SENT TO LLM"
#             )

#             print(
#                 "=" * 80
#             )

#             print(
#                 document_context
#             )

#         if knowledge_context:

#             print(
#                 "\n" + "=" * 80
#             )

#             print(
#                 "KNOWLEDGE CONTEXT SENT TO LLM"
#             )

#             print(
#                 "=" * 80
#             )

#             print(
#                 knowledge_context
#             )

#         # ==================================================
#         # 7. BUILD FINAL PROMPT
#         # ==================================================

#         conversation_context = (
#             self.build_conversation_context()
#         )

#         user_prompt = build_user_prompt(

#             query=query,

#             document_context=
#                 document_context,

#             conversation_context=
#                 conversation_context,

#             operation=
#                 operation,

#             knowledge_context=
#                 knowledge_context

#         )

#         # ==================================================
#         # 8. FINAL LLM
#         # ==================================================

#         print(
#             "\nSending final context to Groq..."
#         )

#         response = (
#             self.client
#             .chat
#             .completions
#             .create(

#                 model=
#                     Config.GROQ_MODEL,

#                 messages=[

#                     {
#                         "role":
#                             "system",

#                         "content":
#                             SYSTEM_PROMPT
#                     },

#                     {
#                         "role":
#                             "user",

#                         "content":
#                             user_prompt
#                     }

#                 ],

#                 temperature=0
#             )
#         )

#         raw_answer = (
#             response
#             .choices[0]
#             .message
#             .content
#             .strip()
#         )

#         print(
#             "\n" + "=" * 80
#         )

#         print(
#             "RAW GROQ RESPONSE"
#         )

#         print(
#             "=" * 80
#         )

#         print(
#             repr(raw_answer)
#         )

#         # ==================================================
#         # 9. PARSE ANSWER
#         # ==================================================

#         answer = (
#             self.parse_llm_response(
#                 raw_answer
#             )
#         )

#         # ==================================================
#         # 10. SAVE CONVERSATION
#         # ==================================================

#         self.save_conversation(

#             query,

#             self.answer_to_text(
#                 answer
#             )

#         )

#         # ==================================================
#         # 11. SOURCES
#         # ==================================================

#         document_sources = (
#             self.build_sources(
#                 document_results
#             )
#         )

#         knowledge_sources = (
#             self.build_knowledge_sources(
#                 knowledge_results
#             )
#         )

#         # ==================================================
#         # 12. RETURN
#         # ==================================================

#         return {

#             "answer":
#                 answer,

#             "document_based":
#                 bool(document_context),

#             "knowledge_based":
#                 bool(knowledge_context),

#             "route":
#                 route,

#             "operation":
#                 operation,

#             "sources":
#                 document_sources,

#             "knowledge_sources":
#                 knowledge_sources,

#             "selected_chunks":
#                 document_results

#         }

















































import json

from groq import Groq
from translator import Translator
from config import Config
from retrieval import Retriever
from context_selector import ContextSelector
from knowledge_retrieval import KnowledgeRetriever

from prompts import (
    SYSTEM_PROMPT,
    ROUTER_SYSTEM_PROMPT,
    build_user_prompt,
    build_router_prompt
)


class LegalEngine:

    def __init__(self):

        # ==================================================
        # GROQ
        # ==================================================

        api_key = Config.GROQ_API_KEY

        if not api_key:
            raise ValueError(
                "GROQ_API_KEY is not configured."
            )

        self.client = Groq(
            api_key=api_key
        )

        # ==================================================
        # DOCUMENT RETRIEVAL
        # ==================================================

        self.retriever = Retriever()

        self.selector = ContextSelector()

        # ==================================================
        # KNOWLEDGE RETRIEVAL
        # ==================================================

        self.knowledge_retriever = KnowledgeRetriever()

        self.knowledge_retriever.initialize()

        # ==================================================
        # TRANSLATOR
        # ==================================================

        self.translator = Translator()

        # ==================================================
        # DOCUMENT STATE
        # ==================================================

        self.loaded = False

        # ==================================================
        # CONVERSATION MEMORY
        # ==================================================

        self.conversation_history = []

        self.max_history = 6

    # ======================================================
    # CONVERSATION CONTEXT
    # ======================================================

    def build_conversation_context(self):

        if not self.conversation_history:
            return ""

        history = []

        for item in self.conversation_history[
            -self.max_history:
        ]:

            history.append(
                f"""
USER:
{item["query"]}

ASSISTANT:
{item["answer"]}
""".strip()
            )

        return "\n\n---\n\n".join(history)

    # ======================================================
    # SAVE CONVERSATION
    # ======================================================

    def save_conversation(
        self,
        query,
        answer
    ):

        self.conversation_history.append({

            "query": query,

            "answer": answer
        })

        self.conversation_history = (
            self.conversation_history[
                -self.max_history:
            ]
        )

    # ======================================================
    # DOCUMENT INGESTION
    # ======================================================

    def load_document(
        self,
        records
    ):

        if not records:

            raise ValueError(
                "No document records were found."
            )

        chunks = self.retriever.create_chunks(
            records
        )

        if not chunks:

            raise ValueError(
                "No chunks could be created from "
                "the document."
            )

        self.retriever.build_index(
            chunks
        )

        self.loaded = True

        # Reset conversation when a new document is loaded.

        self.conversation_history = []

        print(
            "\nDocument successfully loaded."
        )

    # ======================================================
    # BUILD DOCUMENT CONTEXT
    # ======================================================

    def build_context(
        self,
        selected_results
    ):

        if not selected_results:
            return ""

        ordered_results = sorted(
            selected_results,
            key=lambda x: (
                x.get("source", ""),
                x.get("page", 0),
                x.get("page_chunk_position", 0),
                x.get("chunk_id", 0)
            )
        )

        context_parts = []

        for position, result in enumerate(
            ordered_results,
            start=1
        ):

            source = result.get(
                "source",
                "Unknown"
            )

            page = result.get(
                "page",
                "Unknown"
            )

            chunk_id = result.get(
                "chunk_id",
                "Unknown"
            )

            text = result.get(
                "text",
                ""
            ).strip()

            if not text:
                continue

            context_parts.append(
                f"""
[CONTEXT {position}]
Source: {source}
Page: {page}
Chunk ID: {chunk_id}

{text}
""".strip()
            )

        return "\n\n---\n\n".join(
            context_parts
        )

    # ======================================================
    # BUILD DOCUMENT SOURCES
    # ======================================================

    def build_sources(
        self,
        selected_results
    ):

        sources = []

        seen = set()

        for result in selected_results:

            source = result.get("source")
            page = result.get("page")
            chunk_id = result.get("chunk_id")

            if source is None:
                continue

            source_key = (
                source,
                page,
                chunk_id
            )

            if source_key in seen:
                continue

            seen.add(source_key)

            sources.append({

                "source": source,

                "page": page,

                "chunk_id": chunk_id
            })

        return sources

    # ======================================================
    # BUILD KNOWLEDGE CONTEXT
    # ======================================================

    def build_knowledge_context(
        self,
        knowledge_results
    ):

        if not knowledge_results:
            return ""

        context_parts = []

        for position, result in enumerate(
            knowledge_results,
            start=1
        ):

            question = result.get(
                "question",
                ""
            )

            answer = result.get(
                "answer",
                ""
            )

            source = result.get(
                "source",
                "unknown"
            )

            score = result.get(
                "score"
            )

            context_parts.append(
                f"""
[KNOWLEDGE {position}]

Source: {source}
Relevance Score: {score}

Question:
{question}

Answer:
{answer}
""".strip()
            )

        return "\n\n---\n\n".join(
            context_parts
        )

    # ======================================================
    # BUILD KNOWLEDGE SOURCES
    # ======================================================

    def build_knowledge_sources(
        self,
        knowledge_results
    ):

        sources = []

        for result in knowledge_results:

            sources.append({

                "knowledge_id":
                    result.get("knowledge_id"),

                "source":
                    result.get("source"),

                "score":
                    result.get("score"),

                "question":
                    result.get("question")
            })

        return sources

    # ======================================================
    # PARSE STRUCTURED LLM RESPONSE
    # ======================================================

    def parse_llm_response(
        self,
        raw_response
    ):

        if not raw_response:

            return {
                "type": "response",
                "content": [
                    {
                        "type": "paragraph",
                        "text": "No answer was generated."
                    }
                ]
            }

        raw_response = raw_response.strip()

        # --------------------------------------------------
        # Remove code fences
        # --------------------------------------------------

        if raw_response.startswith("```json"):

            raw_response = raw_response[
                len("```json"):
            ].strip()

        elif raw_response.startswith("```"):

            raw_response = raw_response[
                len("```"):
            ].strip()

        if raw_response.endswith("```"):

            raw_response = raw_response[
                :-3
            ].strip()

        # --------------------------------------------------
        # Parse JSON
        # --------------------------------------------------

        try:

            parsed = json.loads(
                raw_response
            )

            if not isinstance(
                parsed,
                dict
            ):

                raise ValueError(
                    "LLM response is not a JSON object."
                )

            answer_type = parsed.get(
                "type",
                "mixed"
            )

            content = parsed.get(
                "content",
                []
            )

            if answer_type not in {
                "mixed",
                "response"
            }:

                answer_type = "mixed"

            if (
                not isinstance(content, list)
                or not content
            ):

                raise ValueError(
                    "Invalid or empty content."
                )

            return {

                "type": answer_type,

                "content": content
            }

        except (
            json.JSONDecodeError,
            ValueError
        ):

            print(
                "\nWarning: LLM returned invalid JSON."
            )

            print(
                "Raw response:"
            )

            print(
                raw_response
            )

            return {

                "type": "response",

                "content": [

                    {
                        "type": "paragraph",

                        "text": raw_response
                    }

                ]
            }

    # ======================================================
    # ANSWER TO TEXT
    # ======================================================

    def answer_to_text(
        self,
        answer
    ):

        if not isinstance(
            answer,
            dict
        ):

            return str(answer)

        texts = []

        for item in answer.get(
            "content",
            []
        ):

            item_type = item.get(
                "type"
            )

            if item_type in {
                "paragraph",
                "heading",
                "warning"
            }:

                text = item.get(
                    "text",
                    ""
                )

                if text:
                    texts.append(text)

            elif item_type in {
                "bullet_list",
                "numbered_list"
            }:

                items = item.get(
                    "items",
                    []
                )

                for text in items:

                    if text:

                        texts.append(
                            f"- {text}"
                        )

        return "\n".join(texts)

    # ======================================================
    # DETERMINE ROUTE
    # ======================================================

    def determine_route(
        self,
        query,
        operation="DOCUMENT_QA"
    ):

        conversation_context = (
            self.build_conversation_context()
        )

        router_prompt = build_router_prompt(

            query=query,

            conversation_context=
                conversation_context,

            document_loaded=
                self.loaded,

            operation=
                operation
        )

        try:

            response = (
                self.client
                .chat
                .completions
                .create(

                    model=Config.GROQ_MODEL,

                    messages=[

                        {
                            "role": "system",

                            "content":
                                ROUTER_SYSTEM_PROMPT
                        },

                        {
                            "role": "user",

                            "content":
                                router_prompt
                        }
                    ],

                    temperature=0
                )
            )

            raw_route = (
                response
                .choices[0]
                .message
                .content
                .strip()
            )

            # --------------------------------------------------
            # Remove code fences
            # --------------------------------------------------

            if raw_route.startswith(
                "```json"
            ):

                raw_route = raw_route[
                    len("```json"):
                ].strip()

            elif raw_route.startswith(
                "```"
            ):

                raw_route = raw_route[
                    len("```"):
                ].strip()

            if raw_route.endswith(
                "```"
            ):

                raw_route = raw_route[
                    :-3
                ].strip()

            parsed = json.loads(
                raw_route
            )

            route = parsed.get(
                "route",
                "KNOWLEDGE"
            ).upper()

            if route not in {
                "DOCUMENT",
                "KNOWLEDGE",
                "BOTH"
            }:

                route = "KNOWLEDGE"

            # --------------------------------------------------
            # Safety fallback
            # --------------------------------------------------

            if (
                route in {
                    "DOCUMENT",
                    "BOTH"
                }
                and not self.loaded
            ):

                route = "KNOWLEDGE"

            print(
                f"\nSelected RAG route: {route}"
            )

            return route

        except Exception as e:

            print(
                f"\nRouting failed: {e}"
            )

            # Safe fallback

            if self.loaded:

                return "DOCUMENT"

            return "KNOWLEDGE"

    # ======================================================
    # ASK QUESTION
    # ======================================================

    def ask(
    self,
    query,
    operation="DOCUMENT_QA",
    language="en"
    ):

        # ==================================================
        # QUERY VALIDATION
        # ==================================================

        if not query or not query.strip():

            return {

                "answer": (
                    "Please enter a question."
                ),

                "sources": []
            }

        query = query.strip()

        # ==================================================
        # LANGUAGE
        # ==================================================

        language = (
            language
            if isinstance(language, str)
            else "en"
        )

        language = language.strip().lower()

        if language not in {
            "en",
            "hi"
        }:
            language = "en"


        # # ==================================================
        # # TRANSLATE QUERY TO ENGLISH
        # # ==================================================

        # original_query = query

        # print(
        #     "\nTranslating query to English..."
        # )

        # query = (
        #     self.translator
        #     .translate_to_english(query)
        # )

        # print(
        #     f"Translated query: {query}"
        # )



      # ==================================================
        # TRANSLATE QUERY TO ENGLISH
        # ==================================================

        original_query = query

        if self.translator.is_hindi(query):

            print(
                "\nHindi query detected. "
                "Translating to English..."
            )

            query = (
                self.translator
                .translate_to_english(query)
            )

            print(
                f"Translated query: {query}"
            )

        else:

            print(
                "\nEnglish query detected - "
                "skipping query translation."
            )

        # ==================================================
        # NORMALIZE OPERATION
        # ==================================================

        operation = (
            operation
            if isinstance(operation, str)
            else "DOCUMENT_QA"
        )

        operation = operation.strip().upper()

        allowed_operations = {

            "DOCUMENT_QA",

            "SUMMARY",

            "CLAUSE_EXPLANATION",

            "RISK_DETECTION",

            "LEGAL_VALIDATION",

            "GENERAL_LEGAL_QA"
        }

        if operation not in allowed_operations:

            operation = "DOCUMENT_QA"

        # ==================================================
        # ROUTING
        # ==================================================

        print(
            "\n" + "=" * 80
        )

        print(
            "LEGAL ENGINE - ROUTING"
        )

        print(
            "=" * 80
        )

        route = self.determine_route(
            query=query,
            operation=operation
        )

        # ==================================================
        # DOCUMENT VARIABLES
        # ==================================================

        selected_results = []

        document_context = ""

        document_sources = []

        # ==================================================
        # KNOWLEDGE VARIABLES
        # ==================================================

        knowledge_results = []

        knowledge_context = ""

        knowledge_sources = []

        # ==================================================
        # DOCUMENT RETRIEVAL
        # ==================================================

        if route in {
            "DOCUMENT",
            "BOTH"
        }:

            if not self.loaded:

                # Safety fallback

                route = "KNOWLEDGE"

            else:

                print(
                    "\nDocument retrieval selected."
                )

                # --------------------------------------------------
                # SUMMARY
                # --------------------------------------------------

                if operation == "SUMMARY":

                    print(
                        "\nSummary operation detected."
                    )

                    results = (
                        self.retriever
                        .get_all_chunks()
                    )

                    print(
                        f"Summary retrieved chunks: "
                        f"{len(results)}"
                    )

                # --------------------------------------------------
                # NORMAL DOCUMENT SEARCH
                # --------------------------------------------------

                else:

                    results = (
                        self.retriever.search(
                            query,
                            include_neighbors=True
                        )
                    )

                if results:

                    # --------------------------------------------------
                    # RERANKING
                    # --------------------------------------------------

                    if operation == "SUMMARY":

                        print(
                            "\nSkipping reranking for summary."
                        )

                        reranked_results = results

                    else:

                        print(
                            "\nReranking candidate chunks..."
                        )

                        reranked_results = (
                            self.selector.rerank(
                                query,
                                results
                            )
                        )

                    # --------------------------------------------------
                    # RELEVANCE
                    # --------------------------------------------------

                    if operation == "SUMMARY":

                        selected_results = (
                            reranked_results
                        )

                    else:

                        if not self.selector.is_relevant(
                            reranked_results
                        ):

                            print(
                                "\nDocument retrieval "
                                "did not pass relevance gate."
                            )

                            selected_results = []

                        else:

                            selected_results = (
                                self.selector.select(
                                    reranked_results
                                )
                            )

                    if selected_results:

                        document_context = (
                            self.build_context(
                                selected_results
                            )
                        )

                        document_sources = (
                            self.build_sources(
                                selected_results
                            )
                        )

        # ==================================================
        # KNOWLEDGE RETRIEVAL
        # ==================================================

        if route in {
            "KNOWLEDGE",
            "BOTH"
        }:

            print(
                "\nKnowledge retrieval selected."
            )

            knowledge_results = (
                self.knowledge_retriever.search(
                    query,
                    top_k=Config.KNOWLEDGE_TOP_K
                )
            )

            # --------------------------------------------------
            # RERANK KNOWLEDGE
            # --------------------------------------------------

            if knowledge_results:

                print(
                    "\nReranking knowledge results..."
                )

                reranked_knowledge = (
                    self.selector.rerank_knowledge(
                        query,
                        knowledge_results
                    )
                )

                # --------------------------------------------------
                # KNOWLEDGE RELEVANCE GATE
                # --------------------------------------------------

                knowledge_results = (
                    self.selector.filter_relevant_knowledge(
                        reranked_knowledge
                    )
                )

            else:

                knowledge_results = []

            knowledge_context = (
                self.build_knowledge_context(
                    knowledge_results
                )
            )

            knowledge_sources = (
                self.build_knowledge_sources(
                    knowledge_results
                )
            )

            print(
                f"Knowledge results: "
                f"{len(knowledge_results)}"
            )

        # ==================================================
        # CHECK CONTEXT
        # ==================================================

        if not document_context and not knowledge_context:

            return {

                "answer": (
                    "I could not find relevant "
                    "information in the available sources."
                ),

                "document_based":
                    route in {
                        "DOCUMENT",
                        "BOTH"
                    },

                "knowledge_based":
                    bool(knowledge_results),

                "operation":
                    operation,

                "sources": [],

                "selected_chunks": []
            }

        # ==================================================
        # DEBUG CONTEXT
        # ==================================================

        print(
            "\n" + "=" * 80
        )

        print(
            "FINAL DOCUMENT CONTEXT"
        )

        print(
            "=" * 80
        )

        if document_context:

            print(
                document_context
            )

        else:

            print(
                "No document context."
            )

        print(
            "\n" + "=" * 80
        )

        print(
            "FINAL KNOWLEDGE CONTEXT"
        )

        print(
            "=" * 80
        )

        if knowledge_context:

            print(
                knowledge_context
            )

        else:

            print(
                "No knowledge context."
            )

        # ==================================================
        # BUILD PROMPT
        # ==================================================

        conversation_context = (
            self.build_conversation_context()
        )

        user_prompt = build_user_prompt(

            query=query,

            context=document_context,

            conversation_context=
                conversation_context,

            operation=operation,

            knowledge_context=
                knowledge_context
        )

        # ==================================================
        # CALL GROQ
        # ==================================================

        print(
            "\nSending context to Groq..."
        )

        response = (
            self.client
            .chat
            .completions
            .create(

                model=Config.GROQ_MODEL,

                messages=[

                    {
                        "role": "system",

                        "content":
                            SYSTEM_PROMPT
                    },

                    {
                        "role": "user",

                        "content":
                            user_prompt
                    }
                ],

                temperature=0
            )
        )

        raw_answer = (
            response
            .choices[0]
            .message
            .content
            .strip()
        )

        # ==================================================
        # PARSE RESPONSE
        # ==================================================

        answer = self.parse_llm_response(
            raw_answer
        )

        # ==================================================
        # TRANSLATE ANSWER
        # ==================================================

        if language == "hi":

            print(
                "\nTranslating answer to Hindi..."
            )

            answer = (
                self.translator
                .translate_answer(
                    answer,
                    language
                )
            )

        print(
            "\n" + "=" * 80
        )

        print(
            "RAW GROQ RESPONSE"
        )

        print(
            "=" * 80
        )

        print(
            repr(raw_answer)
        )

        # ==================================================
        # SAVE CONVERSATION
        # ==================================================

        self.save_conversation(

            query,

            self.answer_to_text(
                answer
            )
        )

        # ==================================================
        # RETURN
        # ==================================================

        return {

            "answer":
                answer,

            "document_based":
                route in {
                    "DOCUMENT",
                    "BOTH"
                },

            "knowledge_based":
                bool(knowledge_results),

            "operation":
                operation,

            "route":
                route,

            "sources":
                document_sources,

            "knowledge_sources":
                knowledge_sources,

            "selected_chunks":
                selected_results
        }