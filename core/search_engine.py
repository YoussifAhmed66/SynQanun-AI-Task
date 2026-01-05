import os
import sys
# Add project root to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import os
from config.settings import Settings
from core.vector_store import VectorStore
from core.embedder import Embedder

class SearchEngine:
    def __init__(self, embedder: Embedder):
        # Loading chromadb
        # self.embedder = embedder
        self.store = VectorStore(embedder, collection_name="legal_docs")
        print(f"Search Engine Ready. Total documents: {self.store.collection.count()}")

    def search(self, query, k=5, threshold=0.7):
        """
        Searches at the chunk level and groups matches into document-level results.
        Returns a list of documents, where each document contains its relevant chunks.
        The total number of chunks returned across all documents is capped at k.
        """
        # Retrieve top k chunks
        results = self.store.search(query, k=k, threshold=threshold)
        
        # Group by document (source)
        doc_map = {}
        # List to maintain the order of documents based on their highest scoring chunk
        doc_order = []
        
        for item, score in results:
            source = item.get('source', 'unknown')
            
            if source not in doc_map:
                doc_map[source] = {
                    'source': source,
                    'type': item.get('type', 'unknown'),
                    'max_score': score,
                    'chunks': []
                }
                doc_order.append(source)
            
            # Add this chunk to the document's list
            doc_map[source]['chunks'].append({
                'text': item.get('text', ''),
                'score': score,
                'metadata': {meta_k: v for meta_k, v in item.items() if meta_k not in ['text', 'score', 'source', 'type']}
            })
            
        # Return documents in original order (best hits first)
        return [doc_map[source] for source in doc_order]

