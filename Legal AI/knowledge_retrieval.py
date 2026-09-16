import json
import os

import faiss
import numpy as np
from embedding_service import EmbeddingService
from config import Config


class KnowledgeRetriever:

    def __init__(self, dataset_path=None):

        # ==================================================
        # DATASET PATH
        # ==================================================

        self.dataset_path = (
            dataset_path
            if dataset_path is not None
            else Config.KNOWLEDGE_DATASET_PATH
        )

        # ==================================================
        # EMBEDDING MODEL
        # ==================================================

        print(
            f"Using Hugging Face embedding API: "
            f"{Config.EMBEDDING_MODEL}"
        )

        self.embedder = EmbeddingService()
        # ==================================================
        # STATE
        # ==================================================

        self.index = None
        self.records = []

    # ==================================================
    # LOAD KNOWLEDGE DATASET
    # ==================================================

    def load_dataset(self):

        if not os.path.exists(self.dataset_path):

            raise FileNotFoundError(
                f"Knowledge dataset not found: "
                f"{self.dataset_path}"
            )

        with open(
            self.dataset_path,
            "r",
            encoding="utf-8"
        ) as file:

            data = json.load(file)

        if not isinstance(data, list):

            raise ValueError(
                "Knowledge dataset must contain "
                "a JSON list."
            )

        cleaned_records = []

        for index, record in enumerate(data):

            if not isinstance(record, dict):
                continue

            question = str(
                record.get("question", "")
            ).strip()

            answer = str(
                record.get("answer", "")
            ).strip()

            source = str(
                record.get("source", "unknown")
            ).strip()

            if not question or not answer:
                continue

            cleaned_records.append({

                "knowledge_id": len(
                    cleaned_records
                ),

                "question": question,

                "answer": answer,

                "source": source,

                "text": (
                    f"Question: {question}\n"
                    f"Answer: {answer}"
                )
            })

        if not cleaned_records:

            raise ValueError(
                "No valid knowledge records "
                "were found."
            )

        self.records = cleaned_records

        print(
            f"Loaded {len(self.records)} "
            f"knowledge records."
        )

        return self.records

    # ==================================================
    # BUILD FAISS INDEX
    # ==================================================

    def build_index(self):

        if not self.records:

            raise ValueError(
                "No knowledge records available. "
                "Call load_dataset() first."
            )

        texts = [
            record["text"]
            for record in self.records
        ]

        print(
            "\nGenerating knowledge embeddings..."
        )

        embeddings = self.embedder.encode(
            texts,
            convert_to_numpy=True,
            normalize_embeddings=True,
            show_progress_bar=True
        )

        embeddings = embeddings.astype(
            "float32"
        )

        dimension = embeddings.shape[1]

        self.index = faiss.IndexFlatIP(
            dimension
        )

        self.index.add(
            embeddings
        )

        print(
            f"Knowledge FAISS index created "
            f"with {len(self.records)} records."
        )

    # ==================================================
    # INITIALIZE
    # ==================================================

    def initialize(self):

        if self.load_index():

            print(
                "Using existing knowledge index."
            )

            return

        print(
            "Knowledge index not found."
        )

        print(
            "Building knowledge index..."
        )

        self.load_dataset()

        self.build_index()

        self.save_index()
    # ==================================================
    # SEARCH
    # ==================================================

    def search(
        self,
        query,
        top_k=None
    ):

        if self.index is None:

            raise RuntimeError(
                "Knowledge FAISS index has not "
                "been created."
            )

        if not query or not query.strip():

            return []

        query = query.strip()

        top_k = (
            top_k
            if top_k is not None
            else Config.KNOWLEDGE_TOP_K
        )

        top_k = min(
            top_k,
            len(self.records)
        )

        # ==================================================
        # QUERY EMBEDDING
        # ==================================================

        query_embedding = self.embedder.encode(
            [query],
            convert_to_numpy=True,
            normalize_embeddings=True
        ).astype("float32")

        # ==================================================
        # FAISS SEARCH
        # ==================================================

        scores, indices = self.index.search(
            query_embedding,
            top_k
        )

        results = []

        for score, index in zip(
            scores[0],
            indices[0]
        ):

            if index < 0:
                continue

            record = self.records[
                int(index)
            ].copy()

            record["score"] = float(
                score
            )

            record["retrieved"] = True

            results.append(
                record
            )

        return results

    # ==================================================
    # GET ALL RECORDS
    # ==================================================

    def get_all_records(self):

        if not self.records:
            return []

        return [
            record.copy()
            for record in self.records
        ]

    
    def save_index(self):

        os.makedirs(
            os.path.dirname(Config.KNOWLEDGE_INDEX_PATH),
            exist_ok=True
        )

        faiss.write_index(
            self.index,
            Config.KNOWLEDGE_INDEX_PATH
        )

        with open(
            Config.KNOWLEDGE_RECORDS_PATH,
            "w",
            encoding="utf-8"
        ) as file:

            json.dump(
                self.records,
                file,
                ensure_ascii=False,
                indent=2
            )

        print(
            "\nKnowledge index saved successfully."
        )


    def load_index(self):

        if not os.path.exists(
            Config.KNOWLEDGE_INDEX_PATH
        ):
            return False

        if not os.path.exists(
            Config.KNOWLEDGE_RECORDS_PATH
        ):
            return False

        self.index = faiss.read_index(
            Config.KNOWLEDGE_INDEX_PATH
        )

        with open(
            Config.KNOWLEDGE_RECORDS_PATH,
            "r",
            encoding="utf-8"
        ) as file:

            self.records = json.load(file)

        print(
            f"Loaded knowledge FAISS index "
            f"with {len(self.records)} records."
        )

        return True