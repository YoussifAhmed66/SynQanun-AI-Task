import os
import sys
# Add project root to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import glob
from tqdm import tqdm

from config.settings import Settings
from utils.load_docx import check_file
from core.chunker import Chunker
from core.vector_store import VectorStore

def run_pipeline():
    """
    Main data ingestion function.
    1. Scan document folders.
    2. Extract text.
    3. Chunk text.
    4. Send chunks to VectorStore (which embeds and adds them to ChromaDB).
    """

    # Initialize Components
    chunker = Chunker()
    
    store = VectorStore(collection_name="legal_docs")
    store.reset()
    
    # Define Source Folders
    sources = {
        "laws": Settings.laws,
        "judgments": Settings.judgments,
        "fatwas": Settings.fatwas
    }

    # Processing Loop
    for category, folder_path in sources.items():
        print(f"Processing Category: {category.upper()}")
        
        docx_files = glob.glob(os.path.join(folder_path, "*.docx"))
        
        batch_chunks = []
        BATCH_SIZE = 32 
        
        for file_path in tqdm(docx_files, desc=f"Loading {category}"):
            file_name = os.path.basename(file_path)
            
            # Extract and chunk Text
            text = check_file(file_path, "Pipeline")
            if not text:
                continue

            # Chunking Text upon it's category
            if category == "laws":
                file_chunks = chunker.chunk_law(text, file_name)
            else:
                # Judgments and Fatwas
                file_chunks = chunker.chunk_recursive(text, file_name, doc_type=category)
            
            batch_chunks.extend(file_chunks)
            
            # Process Batch if full
            if len(batch_chunks) >= BATCH_SIZE:
                 # Pass chunks to VectorStore to embed and save to ChromaDB
                store.add_documents(batch_chunks)
                batch_chunks = [] # Clear batch
                
        # Process remaining chunks
        if batch_chunks:
            store.add_documents(batch_chunks)
            
        print(f"Finished processing {category}.")
        
    print(f"Pipeline Execution Completed. Total documents in collection: {store.collection.count()}")

if __name__ == "__main__":
    run_pipeline()
