import numpy as np
import logging
from typing import List
from fastapi import HTTPException

class EmbeddingGenerator:
    def __init__(self, config, logger=None):
        self.config = config
        self.logger = logger or logging.getLogger(__name__)

    def generate_embeddings(self, model, texts: list, desc="Generating embeddings") -> np.ndarray:
        if not texts:
            return np.array([])

        try:
            all_embeddings = []
            batch_size = self.config.get("BATCH_SIZE", 32)
            self.logger.info(f"Generating embeddings for {len(texts)} texts...")

            for i in range(0, len(texts), batch_size):
                batch_texts = texts[i:i + batch_size]
                batch_embeddings = model.encode(
                    batch_texts,
                    batch_size=batch_size,
                    show_progress_bar=True,
                    convert_to_numpy=True,
                    normalize_embeddings=True
                )

                all_embeddings.append(batch_embeddings)

            embeddings_array = np.vstack(all_embeddings)
            self.logger.info(f"✓ Generated embeddings shape: {embeddings_array.shape}")
            return embeddings_array

        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Embedding generation failed: {str(e)}")
