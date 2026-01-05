import os
import sys
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
import uvicorn
from pydantic import BaseModel
from typing import List, Optional

# Add project root to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.search_engine import SearchEngine
from core.data_pipeline import run_pipeline
from config.settings import Settings
from core.embedder import Embedder

# --- Global State ---
# This dictionary will hold the SearchEngine instance to persist across requests
state = {
    "search_engine": None
}

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Startup: Load SearchEngine (and thus Embedder/ChromaDB) once.
    Checks if the database is empty; if so, triggers data ingestion pipeline.
    """
    print("API Starting up: Loading Models and Database.")
    try:
        # Initial search engine 
        embedder = Embedder()
        engine = SearchEngine(embedder)
        
        # Check if database is empty
        if engine.store.collection.count() == 0:
            print("\nDatabase is empty. Triggering initial ingestion pipeline")
            run_pipeline()
            # Reload engine to pick up new data
            engine = SearchEngine()
        
        state["search_engine"] = engine
        print("API Startup Complete: Search Engine Ready.")
    except Exception as e:
        print(f"CRITICAL: Failed to initialize Search Engine: {e}")
    
    yield
    
    print("API Shutting down.")

app = FastAPI(
    title="SynQanun Task: Legal Search API",
    lifespan=lifespan
)

# --- Models ---

class QueryRequest(BaseModel):
    q: str
    topK: int = 5
    threshold: float = 0.7

class ChunkMatch(BaseModel):
    text: str
    score: float
    metadata: dict

class DocumentResult(BaseModel):
    source: str
    type: str
    max_score: float
    chunks: List[ChunkMatch]

class QueryResponse(BaseModel):
    q: str
    results: List[DocumentResult]

# --- Endpoints ---

@app.get("/")
async def health_check():
    return {"status": "online", "model": Settings.embedding_model}

@app.post("/search", response_model=QueryResponse)
async def search(request: QueryRequest):

    if state["search_engine"] is None:
        raise HTTPException(status_code=503, detail="Search engine not initialized")
    
    try:
        raw_results = state["search_engine"].search(
            query=request.q, 
            k=request.topK, 
            threshold=request.threshold
        )
        
        return QueryResponse(
            q=request.q,
            results=[DocumentResult(**res) for res in raw_results]
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))



if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
