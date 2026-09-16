import time
import numpy as np
from huggingface_hub import InferenceClient

from config import Config


class EmbeddingService:

    def __init__(self):

        if not Config.HF_TOKEN:
            raise ValueError(
                "HF_TOKEN is not configured in the .env file."
            )

        print(
            f"Using Hugging Face embedding API: "
            f"{Config.EMBEDDING_MODEL}"
        )

        self.client = InferenceClient(
            provider="hf-inference",
            api_key=Config.HF_TOKEN
        )

        self.batch_size = 16
        self.max_retries = 3

    def encode(
        self,
        texts,
        convert_to_numpy=True,
        normalize_embeddings=True,
        show_progress_bar=False
    ):

        # Accept a single string
        if isinstance(texts, str):
            texts = [texts]

        if not texts:
            return np.empty(
                (0, 384),
                dtype=np.float32
            )

        all_embeddings = []

        total = len(texts)

        for start in range(
            0,
            total,
            self.batch_size
        ):

            batch = texts[
                start:start + self.batch_size
            ]

            batch_number = (
                start // self.batch_size
            ) + 1

            total_batches = (
                (total - 1) // self.batch_size
            ) + 1

            print(
                f"Embedding batch "
                f"{batch_number}/{total_batches} "
                f"({len(batch)} texts)"
            )

            for attempt in range(
                self.max_retries
            ):

                try:

                    embeddings = (
                        self.client.feature_extraction(
                            batch,
                            model=Config.EMBEDDING_MODEL,
                            normalize=normalize_embeddings
                        )
                    )

                    embeddings = np.asarray(
                        embeddings,
                        dtype=np.float32
                    )

                    if embeddings.ndim == 1:
                        embeddings = embeddings.reshape(
                            1, -1
                        )

                    all_embeddings.append(
                        embeddings
                    )

                    break

                except Exception as e:

                    print(
                        f"Embedding request failed "
                        f"(attempt {attempt + 1}/"
                        f"{self.max_retries}): {e}"
                    )

                    if attempt == (
                        self.max_retries - 1
                    ):
                        raise

                    time.sleep(
                        2 ** attempt
                    )

        return np.vstack(
            all_embeddings
        )