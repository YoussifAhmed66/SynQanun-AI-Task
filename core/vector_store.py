import os
import sys
# Add project root to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import chromadb
from chromadb.config import Settings as ChromaSettings
import uuid

from core.embedder import Embedder
from config.settings import Settings

class VectorStore:
    def __init__(self, embedder: Embedder, collection_name="legal_docs"):
        """
        Initializes the ChromaDB client and collection.
        """        
        self.embedder = embedder
        
        self.client = chromadb.PersistentClient(path=Settings.indices_path)

        
        self.collection = self.client.get_or_create_collection(
            name = collection_name, 
            metadata = {"hnsw:space": "cosine"}
        ) 

        self.collection.peek(limit=1)  # Forces the database to load in memory to avoid delay on first query
        
        print(f"Connected to collection: {collection_name}. Count: {self.collection.count()}")

    def add_documents(self, chunks):
        """
        Embeds and adds documents to the ChromaDB collection.
        """
        if not chunks:
            return

        texts = [c['text'] for c in chunks]
        metadatas = [c['metadata'] for c in chunks]
        
        # Generate Unique IDs using UUID
        ids = [str(uuid.uuid4()) for c in chunks]
        
        # Generate Embeddings
        print(f"Embedding {len(texts)} chunks")
        embeddings = self.embedder.embed_texts(texts)
        
        embeddings_list = embeddings.tolist()
        
        # Add to Chromadb
        self.collection.add(
            documents=texts,
            embeddings=embeddings_list,
            metadatas=metadatas,
            ids=ids
        )
        print(f"Added {len(chunks)} documents to ChromaDB.")

    def search(self, query, k=5, threshold=0.6):
        """
        Searches the collection.
        Returns list of (metadata_with_score, score).
        """
        # Embed Query 
        query_vec = self.embedder.embed_query(query)

        # Query Chromadb
        results = self.collection.query(
            query_embeddings=[query_vec.tolist()],
            n_results=k
        )
        
        final_results = []
        
        if results['distances'] and results['distances'][0]:
            distances = results['distances'][0]
            metadatas = results['metadatas'][0]
            documents = results['documents'][0]
            
            for i, dist in enumerate(distances):
                # Convert Cosine Distance to Similarity
                score = 1 - dist
                
                if score >= threshold:
                    meta = metadatas[i]
                    item = meta.copy()
                    item['score'] = round(score, 3)

                    item['text'] = documents[i] 
                    
                    final_results.append((item, score))
                    
        return final_results
        
    def reset(self):
        """Resets (deletes and recreates) the collection."""
        name = self.collection.name
        self.client.delete_collection(name)
        self.collection = self.client.get_or_create_collection(
            name=name, 
            metadata={"hnsw:space": "cosine"}
        )
        print(f"Collection '{name}' reset and recreated.")


    
