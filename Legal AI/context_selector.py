from sentence_transformers import CrossEncoder
from config import Config


class ContextSelector:

    def __init__(self, max_chunks=None, score_gap=None):

        self.max_chunks = (
            max_chunks
            if max_chunks is not None
            else Config.MAX_CONTEXT_CHUNKS
        )

        self.score_gap = (
            score_gap
            if score_gap is not None
            else Config.RERANK_SCORE_MARGIN
        )

        self.reranker_threshold = Config.RERANKER_THRESHOLD

        print(
            f"Loading reranker model: "
            f"{Config.RERANKER_MODEL}"
        )

        self.reranker = CrossEncoder(
            Config.RERANKER_MODEL,
            max_length=512
        )

    # ==================================================
    # RERANK
    # ==================================================

    def rerank(self, query, results):

        if not results:
            return []

        pairs = [
            (query, result["text"])
            for result in results
        ]

        scores = self.reranker.predict(pairs)

        reranked_results = []

        for result, score in zip(results, scores):

            result = result.copy()

            result["reranker_score"] = float(score)

            reranked_results.append(result)

        # Highest relevance first
        reranked_results.sort(
            key=lambda x: x["reranker_score"],
            reverse=True
        )

        return reranked_results

    # ==================================================
    # CHECK RELEVANCE
    # ==================================================

    def is_relevant(self, results):

        if not results:
            return False

        best_score = results[0].get(
            "reranker_score",
            float("-inf")
        )

        print(
            f"\nBest reranker score: {best_score:.4f}"
        )

        print(
            f"Reranker threshold: "
            f"{self.reranker_threshold:.4f}"
        )

        if best_score < self.reranker_threshold:

            print(
                "Query rejected: "
                "no sufficiently relevant chunk found."
            )

            return False

        print(
            "Query accepted: "
            "relevant document context found."
        )

        return True

    # ==================================================
    # SELECT FINAL CONTEXT
    # ==================================================

    def select(self, results):

        if not results:
            return []

        # --------------------------------------------------
        # 1. Remove duplicate chunks
        # --------------------------------------------------

        unique = {}

        for result in results:

            chunk_id = result.get("chunk_id")

            if chunk_id is None:
                continue

            if chunk_id not in unique:

                unique[chunk_id] = result

            else:

                existing = unique[chunk_id]

                existing_score = existing.get(
                    "reranker_score",
                    float("-inf")
                )

                new_score = result.get(
                    "reranker_score",
                    float("-inf")
                )

                if new_score > existing_score:
                    unique[chunk_id] = result

        results = list(unique.values())

        if not results:
            return []

        # --------------------------------------------------
        # 2. Sort by reranker score
        # --------------------------------------------------

        reranked = sorted(
            results,
            key=lambda x: x.get(
                "reranker_score",
                float("-inf")
            ),
            reverse=True
        )

        best_score = reranked[0].get(
            "reranker_score",
            float("-inf")
        )

        # --------------------------------------------------
        # 3. Select chunks close to best score
        # --------------------------------------------------

        selected = []

        for result in reranked:

            score = result.get(
                "reranker_score",
                float("-inf")
            )

            score_difference = best_score - score

            if score_difference <= self.score_gap:

                selected.append(result)

            if len(selected) >= self.max_chunks:
                break

        # --------------------------------------------------
        # 4. Add useful neighbouring chunks
        # --------------------------------------------------

        selected_ids = {
            result["chunk_id"]
            for result in selected
        }

        neighbor_score_gap = self.score_gap * 2

        document_order = sorted(
            results,
            key=lambda x: x.get(
                "chunk_id",
                0
            )
        )

        for result in document_order:

            if len(selected) >= self.max_chunks:
                break

            chunk_id = result.get("chunk_id")

            if chunk_id in selected_ids:
                continue

            score = result.get(
                "reranker_score",
                float("-inf")
            )

            score_difference = best_score - score

            if score_difference > neighbor_score_gap:
                continue

            same_source_neighbor = False

            for selected_result in selected:

                selected_id = selected_result.get(
                    "chunk_id"
                )

                if abs(chunk_id - selected_id) != 1:
                    continue

                if (
                    result.get("source")
                    == selected_result.get("source")
                ):
                    same_source_neighbor = True
                    break

            if same_source_neighbor:

                selected.append(result)
                selected_ids.add(chunk_id)

        # --------------------------------------------------
        # 5. FINAL DOCUMENT ORDER
        # --------------------------------------------------

        selected.sort(
            key=lambda x: (
                x.get("source", ""),
                x.get("page", 0),
                x.get("page_chunk_position", 0),
                x.get("chunk_id", 0)
            )
        )

        # --------------------------------------------------
        # 6. Maximum context limit
        # --------------------------------------------------

        selected = selected[
            :self.max_chunks
        ]

        return selected




        # ==================================================
    # RERANK KNOWLEDGE
    # ==================================================

    def rerank_knowledge(self, query, results):

        if not results:
            return []

        pairs = [
            (
                query,
                f"""
Question:
{result.get("question", "")}

Answer:
{result.get("answer", "")}
""".strip()
            )
            for result in results
        ]

        scores = self.reranker.predict(pairs)

        reranked_results = []

        for result, score in zip(
            results,
            scores
        ):

            result = result.copy()

            result["reranker_score"] = float(
                score
            )

            reranked_results.append(
                result
            )

        # Highest relevance first
        reranked_results.sort(
            key=lambda x: x.get(
                "reranker_score",
                float("-inf")
            ),
            reverse=True
        )

        return reranked_results


    # ==================================================
    # FILTER KNOWLEDGE RELEVANCE
    # ==================================================

    def filter_relevant_knowledge(
        self,
        results
    ):

        if not results:
            return []

        threshold = (
            Config.KNOWLEDGE_RERANKER_THRESHOLD
        )

        relevant = []

        print(
            "\nKnowledge relevance filtering:"
        )

        print(
            f"Knowledge reranker threshold: "
            f"{threshold:.4f}"
        )

        for result in results:

            score = result.get(
                "reranker_score",
                float("-inf")
            )

            print(
                f"\nKnowledge ID: "
                f"{result.get('knowledge_id')}"
            )

            print(
                f"Question: "
                f"{result.get('question', '')}"
            )

            print(
                f"Reranker score: "
                f"{score:.4f}"
            )

            if score >= threshold:

                print(
                    "Result: ACCEPTED"
                )

                relevant.append(result)

            else:

                print(
                    "Result: REJECTED"
                )

        return relevant