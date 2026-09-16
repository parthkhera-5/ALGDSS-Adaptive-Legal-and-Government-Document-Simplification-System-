# import json
# from langchain_core.documents import Document
# from config.config import (TEMPLATE_DIR,DATA_METADATA_DIR,CHROMA_PATH,COLLECTION_NAME)
# from rag.rag_utils import (get_text_splitter,get_vectorstore)
# from utils.utils import (extract_text)

# # ============================================================
# # LOAD METADATA
# # ============================================================
# def load_metadata():
#     metadata_map = {}
#     for file_path in DATA_METADATA_DIR.glob("*.json"):
#         try:
#             with open(file_path, "r", encoding="utf-8") as file:
#                 metadata = json.load(file)
#             template_id = metadata.get("template_id")
#             if not template_id:
#                 print(f"Skipping {file_path.name}: " "template_id missing.")
#                 continue
#             metadata_map[template_id] = metadata
#             print(f"Metadata loaded: " f"{file_path.name}")
#         except Exception as exc:
#             print(f"Failed to read metadata " f"{file_path}: {exc}")
#     return metadata_map

# # ============================================================
# # LOAD LEGAL TEMPLATES
# # ============================================================
# def load_templates():
#     documents = []
#     metadata_map = load_metadata()
#     if not metadata_map:
#         print("No metadata files found.")
#         return documents
#     # --------------------------------------------------------
#     # Process each metadata record
#     # --------------------------------------------------------
#     for template_id, metadata in metadata_map.items():
#         template_file = metadata.get("template_file")
#         document_name = metadata.get("document_name", "Legal Document")
#         document_type = metadata.get("document_type","")
#         version = metadata.get("version","")
#         if not template_file:
#             print(f"Skipping {document_name}: " "template_file missing.")
#             continue
#         template_path = (TEMPLATE_DIR / template_file)
#         # ----------------------------------------------------
#         # Check template
#         # ----------------------------------------------------
#         if not template_path.exists():
#             print(f"Template not found: " f"{template_path}")
#             continue
#         print()
#         print(f"Loading template: " f"{document_name}")
#         # ----------------------------------------------------
#         # Extract DOCX text
#         # ----------------------------------------------------
#         try:
#             text = extract_text(str(template_path))
#         except Exception as exc:
#             print(f"Failed to extract text from " f"{template_file}: {exc}")
#             continue
#         if not text or not text.strip():
#             print(f"Empty document: " f"{template_file}")
#             continue
#         # ----------------------------------------------------
#         # Create LangChain Document
#         # ----------------------------------------------------
#         documents.append(Document(
#                 page_content=text,
#                 metadata={
#                     "template_id":
#                         template_id,
#                     "document_name":
#                         document_name,
#                     "document_type":
#                         document_type,
#                     "version":
#                         version,
#                     "template_file":
#                         template_file
#                 }
#             )
#         )
#         print(f"Loaded successfully: " f"{template_file}")
#     return documents

# # ============================================================
# # MAIN
# # ============================================================
# def main():
#     print()
#     print("=" * 60)
#     print("BUILDING LEGAL DOCUMENT VECTOR DATABASE")
#     print("=" * 60)
#     # --------------------------------------------------------
#     # Load templates
#     # --------------------------------------------------------
#     documents = load_templates()
#     if not documents:
#         print()
#         print("No legal templates were loaded.")
#         return
#     # --------------------------------------------------------
#     # Split documents
#     # --------------------------------------------------------
#     print()
#     print("Creating document chunks...")
#     splitter = get_text_splitter()
#     chunks = splitter.split_documents(documents)
#     print(f"Documents loaded: " f"{len(documents)}")
#     print(f"Chunks created: " f"{len(chunks)}")
#     # --------------------------------------------------------
#     # Create/Get vector store
#     # --------------------------------------------------------
#     print()
#     print("Creating ChromaDB...")
#     vectorstore = get_vectorstore()
#     # --------------------------------------------------------
#     # Add chunks
#     # --------------------------------------------------------
#     vectorstore.add_documents(chunks)
#     # --------------------------------------------------------
#     # Success
#     # --------------------------------------------------------
#     print()
#     print("=" * 60)
#     print("LEGAL DOCUMENTS ADDED TO CHROMADB")
#     print("=" * 60)
#     print()
#     print(f"Database location: " f"{CHROMA_PATH}")
#     print(f"Collection: " f"{COLLECTION_NAME}")
#     print(f"Templates: " f"{len(documents)}")
#     print(f"Chunks: " f"{len(chunks)}")
#     print()

# # ============================================================
# # RUN
# # ============================================================
# if __name__ == "__main__":
#     main()








import json
import re
from langchain_core.documents import Document
from config.config import (TEMPLATE_DIR,DATA_METADATA_DIR,CHROMA_PATH,COLLECTION_NAME,)
from rag.rag_utils import (get_text_splitter,get_vectorstore,)
from utils.utils import extract_text
# ============================================================
# NORMALIZE TEXT
# ============================================================
def normalize_text(text):
    if not text:
        return ""
    text = text.lower().strip()
    text = re.sub(r"\s+", " ", text)
    return text
# ============================================================
# LOAD METADATA
# ============================================================
def load_metadata():
    metadata_map = {}
    for file_path in DATA_METADATA_DIR.glob("*.json"):
        try:
            with open(file_path, "r", encoding="utf-8") as file:
                metadata = json.load(file)
            template_id = metadata.get("template_id")
            if not template_id:
                print(f"Skipping {file_path.name}: template_id missing.")
                continue
            metadata_map[template_id] = metadata
            print(f"Metadata loaded: {file_path.name}")
        except Exception as exc:
            print(f"Failed to read metadata {file_path}: {exc}")
    return metadata_map
# ============================================================
# LOAD LEGAL TEMPLATES
# ============================================================
def load_templates():
    documents = []
    metadata_map = load_metadata()
    if not metadata_map:
        print("No metadata files found.")
        return documents
    for template_id, metadata in metadata_map.items():
        template_file = metadata.get("template_file")
        document_name = metadata.get("document_name", "Legal Document")
        document_type = metadata.get("document_type", "")
        version = metadata.get("version", "")
        if not template_file:
            print(f"Skipping {document_name}: template_file missing.")
            continue
        template_path = TEMPLATE_DIR / template_file
        if not template_path.exists():
            print(f"Template not found: {template_path}")
            continue
        print(f"\nLoading template: {document_name}")
        try:
            text = extract_text(str(template_path))
        except Exception as exc:
            print(f"Failed to extract text from {template_file}: {exc}")
            continue
        if not text.strip():
            print(f"Empty document: {template_file}")
            continue
        # ----------------------------------------------------
        # Standardized metadata
        # ----------------------------------------------------
        normalized_name = normalize_text(document_name)
        normalized_type = normalize_text(document_type)
        documents.append(
            Document(
                page_content=text,
                metadata={
                    "template_id": str(template_id).strip(),
                    "document_name": normalized_name,
                    "document_type": normalized_type,
                    "version": version,
                    "template_file": template_file,
                },
            )
        )
        print(f"Loaded successfully: {template_file}")
    return documents
# ============================================================
# MAIN
# ============================================================
def main():
    print("\n" + "=" * 60)
    print("BUILDING LEGAL DOCUMENT VECTOR DATABASE")
    print("=" * 60)
    documents = load_templates()
    if not documents:
        print("\nNo legal templates were loaded.")
        return
    print("\nCreating document chunks...")
    splitter = get_text_splitter()
    chunks = splitter.split_documents(documents)
    print(f"Documents loaded: {len(documents)}")
    print(f"Chunks created: {len(chunks)}")
    print("\nCreating ChromaDB...")
    vectorstore = get_vectorstore()
    # --------------------------------------------------------
    # Reset old collection
    # --------------------------------------------------------
    try:
        vectorstore.delete_collection()
        print("Old Chroma collection deleted.")
        vectorstore = get_vectorstore()
    except Exception:
        print("No existing collection to delete.")
    # --------------------------------------------------------
    # Add chunks
    # --------------------------------------------------------
    vectorstore.add_documents(chunks)
    print("\n" + "=" * 60)
    print("LEGAL DOCUMENTS ADDED TO CHROMADB")
    print("=" * 60)
    print(f"\nDatabase location: {CHROMA_PATH}")
    print(f"Collection: {COLLECTION_NAME}")
    print(f"Templates: {len(documents)}")
    print(f"Chunks: {len(chunks)}")
# ============================================================
# RUN
# ============================================================
if __name__ == "__main__":
    main()