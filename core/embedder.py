import os
import sys
# Add project root to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sentence_transformers import SentenceTransformer
import numpy as np

from config.settings import Settings

class Embedder:
    def __init__(self, model_name=Settings.embedding_model):
        """
        Initializes the sentence transformer model.
        """
        print(f"Loading embedding model: {model_name}")
        self.model = SentenceTransformer(model_name, trust_remote_code=True)
        
    def embed_texts(self, texts):
        """
        Converts a list of strings into a numpy array of vectors.
        """
        embeddings = self.model.encode(texts, normalize_embeddings=True, show_progress_bar=False)
        return embeddings

    def embed_query(self, query):
        """
        Embeds a single query string directly.
        """
        embedding = self.model.encode(query, normalize_embeddings=True, show_progress_bar=False)
        return embedding

