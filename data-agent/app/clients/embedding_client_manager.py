from typing import Optional

from langchain_huggingface import HuggingFaceEmbeddings

from app.conf.app_config import EmbeddingConfig, app_config


class EmbeddingClientManager:
    def __init__(self, config: EmbeddingConfig):
        self.client: Optional[HuggingFaceEmbeddings] = None
        self.config = config

    def init(self):
        self.client = HuggingFaceEmbeddings(
            model_name=self.config.model,
            model_kwargs={"device": "cpu"},
            encode_kwargs={"normalize_embeddings": True},
        )


embedding_client_manager = EmbeddingClientManager(app_config.embedding)
