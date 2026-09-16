import faiss
import re
import json
from embedding_service import EmbeddingService
from groq import Groq
from config import Config


class Retriever:

    def __init__(self):

            print(
                f"Using Hugging Face embedding API: "
                f"{Config.EMBEDDING_MODEL}"
            )

            self.embedder = EmbeddingService()

            self.client = Groq(
                api_key=Config.GROQ_API_KEY
            )

            self.index = None
            self.chunks = []
    # --------------------------------------------------
    # CHUNKING
    # --------------------------------------------------

    def create_chunks(self, records):

        chunks = []

        TARGET_WORDS = 300
        MAX_WORDS = 400
        OVERLAP_WORDS = 40

        # Track chunk position separately for each page
        page_chunk_positions = {}

        for record in records:

            text = record["text"].strip()

            if not text:
                continue

            text = re.sub(r"\s+", " ", text).strip()

            words = text.split()

            page = record["page"]
            source = record["source"]

            # Get section information from the document parser
            sections = record.get("sections", [])

            # Create a simple section identifier
            if sections:
                section_id = " | ".join(
                    str(section).strip()
                    for section in sections
                )
            else:
                section_id = None

            # Initialize page counter
            page_key = (source, page)

            if page_key not in page_chunk_positions:
                page_chunk_positions[page_key] = 0

            # --------------------------------------------------
            # Short page → one chunk
            # --------------------------------------------------

            if len(words) <= MAX_WORDS:

                position = page_chunk_positions[page_key]

                chunks.append({
                    "chunk_id": len(chunks),
                    "text": text,
                    "page": page,
                    "source": source,
                    "sections": sections,
                    "section_id": section_id,
                    "page_chunk_position": position
                })

                page_chunk_positions[page_key] += 1

                continue

            # --------------------------------------------------
            # Long page → multiple chunks
            # --------------------------------------------------

            start = 0

            while start < len(words):

                end = min(
                    start + TARGET_WORDS,
                    len(words)
                )

                if end < len(words):

                    end = min(
                        start + MAX_WORDS,
                        len(words)
                    )

                chunk_words = words[start:end]

                chunk_text = " ".join(chunk_words)

                # Try to finish at a sentence boundary
                if end < len(words):

                    matches = list(
                        re.finditer(
                            r"[.!?](?:\s|$)",
                            chunk_text
                        )
                    )

                    if matches:

                        last_match = matches[-1]

                        natural_text = (
                            chunk_text[:last_match.end()]
                            .strip()
                        )

                        natural_words = natural_text.split()

                        if len(natural_words) >= 150:

                            chunk_text = natural_text

                            end = (
                                start +
                                len(natural_words)
                            )

                position = page_chunk_positions[page_key]

                chunks.append({
                    "chunk_id": len(chunks),
                    "text": chunk_text,
                    "page": page,
                    "source": source,
                    "sections": sections,
                    "section_id": section_id,
                    "page_chunk_position": position
                })

                page_chunk_positions[page_key] += 1

                next_start = end - OVERLAP_WORDS

                if next_start <= start:
                    next_start = end

                start = next_start

        print(f"Created {len(chunks)} chunks.")

        return chunks
    # --------------------------------------------------
    # BUILD FAISS INDEX
    # --------------------------------------------------

    def build_index(self, chunks):

        if not chunks:
            raise ValueError(
                "No chunks available to index."
            )

        texts = [
            chunk["text"]
            for chunk in chunks
        ]

        embeddings = self.embedder.encode(
            texts,
            convert_to_numpy=True,
            normalize_embeddings=True,
            show_progress_bar=True
        )

        embeddings = embeddings.astype("float32")

        dimension = embeddings.shape[1]

        self.index = faiss.IndexFlatIP(dimension)

        self.index.add(embeddings)

        self.chunks = chunks

        print(
            f"FAISS index created with "
            f"{len(chunks)} chunks."
        )

    # --------------------------------------------------
    # QUERY EXPANSION
    # --------------------------------------------------

    # --------------------------------------------------
# LLM QUERY EXPANSION
# --------------------------------------------------

    def expand_query(self, query):

        prompt = f"""
    You are a legal information retrieval assistant.

    The user has asked the following legal question:

    "{query}"

    Generate exactly 3 alternate search queries that could retrieve
    relevant legal documents for answering the question.

    Rules:
    - Preserve the original legal meaning.
    - Use different legal terminology where appropriate.
    - Include relevant legal synonyms.
    - Do not answer the question.
    - Do not add facts that are not present in the question.
    - Keep each query concise.
    - Return ONLY valid JSON.

    Required format:

    [
        "alternate query 1",
        "alternate query 2",
        "alternate query 3"
    ]
    """

        try:

            response = self.client.chat.completions.create(
                model=Config.GROQ_MODEL,
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You generate search queries for "
                            "legal document retrieval."
                        )
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.2,
            )

            content = response.choices[0].message.content.strip()

            # Remove markdown code fences if returned
            content = re.sub(
                r"```json|```",
                "",
                content
            ).strip()

            alternate_queries = json.loads(content)

            if not isinstance(alternate_queries, list):
                return [query]

            alternate_queries = [
                str(q).strip()
                for q in alternate_queries
                if str(q).strip()
            ]

            # Limit to 3
            alternate_queries = alternate_queries[:3]

            return [query] + alternate_queries

        except Exception as e:

            print(
                f"Query expansion failed: {e}"
            )

            # Always fall back to original query
            return [query]

# --------------------------------------------------
# SEARCH
# --------------------------------------------------

    def search(
        self,
        query,
        top_k=None,
        include_neighbors=True
    ):

        if self.index is None:
            raise RuntimeError(
                "FAISS index has not been created. "
                "Call build_index() first."
            )

        if not query.strip():
            return []

        top_k = top_k or Config.TOP_K

        top_k = min(
            top_k,
            len(self.chunks)
        )

        # --------------------------------------------------
        # 1. Generate alternate queries
        # --------------------------------------------------

        if Config.ENABLE_QUERY_EXPANSION:

            queries = self.expand_query(query)

        else:

            queries = [query]

        print("\n" + "=" * 60)
        print("QUERY EXPANSION")
        print("=" * 60)

        for i, q in enumerate(queries):

            if i == 0:
                print(f"Original  : {q}")
            else:
                print(f"Alternate {i}: {q}")

        # --------------------------------------------------
        # 2. Search FAISS for EVERY query
        # --------------------------------------------------

        all_matches = {}

        for search_query in queries:

            print(
                f"\nSearching FAISS for:\n"
                f"{search_query}"
            )

            query_embedding = self.embedder.encode(
                [search_query],
                convert_to_numpy=True,
                normalize_embeddings=True
            ).astype("float32")

            scores, indices = self.index.search(
                query_embedding,
                top_k
            )

            for score, index in zip(
                scores[0],
                indices[0]
            ):

                if index < 0:
                    continue

                score = float(score)

                # --------------------------------------------------
                # Keep highest score if the same chunk is
                # retrieved by multiple queries
                # --------------------------------------------------

                if (
                    index not in all_matches
                    or score > all_matches[index]
                ):

                    all_matches[index] = score

        # --------------------------------------------------
        # 3. Final retrieved indices
        # --------------------------------------------------

        matched_indices = list(
            all_matches.keys()
        )

        score_map = all_matches

        print(
            f"\nTotal unique FAISS matches: "
            f"{len(matched_indices)}"
        )

        # --------------------------------------------------
        # 4. Add contextual neighbours
        # --------------------------------------------------

        expanded_indices = set(
            matched_indices
        )

        if include_neighbors:

            neighbor_count = Config.NEIGHBOR_COUNT

            for index in matched_indices:

                current = self.chunks[index]

                current_source = current["source"]
                current_section = current.get(
                    "section_id"
                )

                # --------------------------------------------------
                # Look backward
                # --------------------------------------------------

                for offset in range(
                    1,
                    neighbor_count + 1
                ):

                    neighbor_index = index - offset

                    if neighbor_index < 0:
                        continue

                    neighbor = self.chunks[
                        neighbor_index
                    ]

                    # Must belong to same document
                    if (
                        neighbor["source"]
                        != current_source
                    ):
                        continue

                    # Prefer same section
                    if (
                        current_section is not None
                        and neighbor.get("section_id")
                        != current_section
                    ):
                        continue

                    expanded_indices.add(
                        neighbor_index
                    )

                # --------------------------------------------------
                # Look forward
                # --------------------------------------------------

                for offset in range(
                    1,
                    neighbor_count + 1
                ):

                    neighbor_index = index + offset

                    if neighbor_index >= len(
                        self.chunks
                    ):
                        continue

                    neighbor = self.chunks[
                        neighbor_index
                    ]

                    # Must belong to same document
                    if (
                        neighbor["source"]
                        != current_source
                    ):
                        continue

                    # Prefer same section
                    if (
                        current_section is not None
                        and neighbor.get("section_id")
                        != current_section
                    ):
                        continue

                    expanded_indices.add(
                        neighbor_index
                    )

        # --------------------------------------------------
        # 5. Sort in document order
        # --------------------------------------------------

        expanded_indices = sorted(
            expanded_indices
        )

        # --------------------------------------------------
        # 6. Create results
        # --------------------------------------------------

        results = []

        for index in expanded_indices:

            chunk = self.chunks[index].copy()

            if index in score_map:

                chunk["score"] = score_map[index]
                chunk["retrieved"] = True

            else:

                chunk["score"] = None
                chunk["retrieved"] = False

            results.append(chunk)

        # --------------------------------------------------
        # 7. Return AFTER all queries are processed
        # --------------------------------------------------

        return results             # --------------------------------------------------
        # GET ALL CHUNKS
        # --------------------------------------------------

    
    
    def get_all_chunks(self):

        if not self.chunks:
            return []

        return [
            chunk.copy()
            for chunk in self.chunks
        ]