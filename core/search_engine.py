import os
import sys
# Add project root to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import os
from config.settings import Settings
from core.vector_store import VectorStore

class SearchEngine:
    def __init__(self):
        # Loading chromadb
        self.store = VectorStore(collection_name="legal_docs")
        print(f"Search Engine Ready. Total documents: {self.store.collection.count()}")

    def search(self, query, k=5, threshold=0.7):
        """
        Searches the  vector database and returns a list of top results.
        k: Total results to retrieve.
        threshold: Minimum similarity score (0 to 1).
        """
        # Query the vector database
        results = self.store.search(query, k=k, threshold=threshold)
        
        return [item for item, score in results]


# Testing Block
if __name__ == "__main__":
    engine = SearchEngine()
    
    query = "هل يجوز قانوناً خصم قيمة الغرامة المحكوم بها في جريمة رشوة من المعاش اللي بياخده ورثة الموظف بعد وفاته؟"
    print(f"\nSearching for: {query}")
    
    results = engine.search(query, k=5, threshold=0.7)
    
    print(f"\n--- Top Results ({len(results)}) ---")
    for item in results:
        try:
            print(f"[{item['score']}] ({item['type'].upper()}) {item['text']}")
        except UnicodeEncodeError:
            print(f"[{item['score']}] ({item['type'].upper()}) {item['text'].encode('utf-8', 'replace').decode('utf-8')}")
