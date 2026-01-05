# SynQanun: Arabic Legal Semantic Search Engine

SynQanun is a high-performance semantic search pipeline designed specifically for Arabic legal documents, including Laws, Judgments, and Fatwas. 

## Overview

The system transforms raw `.docx` legal documents into a searchable vector database. It uses state-of-the-art multilingual embeddings to understand the *meaning* behind legal queries rather than just matching keywords.

---

## Directory Structure

```text
synqanun/
├── api/
│   └── main.py          # FastAPI application & endpoints
├── config/
│   └── settings.py       # Centralized configuration (paths, model, chunking)
├── core/
│   ├── chunker.py       # Custom logic for Laws and Narrative documents
│   ├── embedder.py      # Sentence-Transformers wrapper
│   ├── search_engine.py  # Unified search interface
│   └── vector_store.py  # ChromaDB management & UUID generation
├── data/                # Source folders for .docx files
│   ├── laws/
│   ├── judgments/
│   └── fatwas/
├── utils/
│   └── load_docx.py      # Text extraction logic
├── vectordb/            # Persistent ChromaDB storage (auto-generated)
└── requirements.txt     # Project dependencies
```

---

## Getting Started

### 1. Setup Virtual Environment
It is recommended to use a virtual environment to manage dependencies:
```bash
# Create the environment
python -m venv venv

# Activate it (Windows)
venv\Scripts\activate

# Activate it (Linux/macOS)
source venv/bin/activate
```

### 2. Install Dependencies
Ensure you have Python 3.9+ installed, then run:
```bash
pip install -r requirements.txt
```

### 3. Prepare Data
Place your `.docx` documents in the corresponding folders in the `data/` directory:
- `data/laws/`
- `data/judgments/`
- `data/fatwas/`

### 4. Build the Index (Ingestion)
You can build the index manually using the command below, or simply **start the API** (see next step). If the API detects an empty database on startup, it will automatically trigger the ingestion pipeline for you.

```bash
python core/data_pipeline.py
```

### 5. Run the API
Start the FastAPI server:
```bash
python api/main.py
```
*Or using uvicorn directly from the root:*
```bash
uvicorn api.main:app --reload
```
You can now access the search interface at `http://127.0.0.1:8000/docs`.

---

## Architecture & Reasoning

### 1. Advanced Chunking Strategy
Chunking is the most critical step in legal search. We employ two distinct strategies based on document structure:

#### **Laws (Structure-Aware Regex)**
- **Method**: We use a specialized Regular Expression `(?:^|\n)(المادة\s+\d+[:\.]?)` to identify "Articles" (المواد).
- **Reasoning**: Legal laws are inherently organized by Articles. An Article is a complete semantic unit of a legal rule. By chunking exactly at Article boundaries, we ensure that a user retrieving a rule gets the *entire* context of that specific article, not just a random snippet if the chunker had cut it in the middle.
- **Safety**: If an article happens to be exceptionally long (e.g., more than 2000 characters), the system automatically triggers a recursive split to ensure the embedding model remains effective.

#### **Judgments & Fatwas (Recursive Character Splitting)**
- **Method**: These documents are often narrative and lack a rigid "Article" structure. We use a **Recursive Character Splitter** that splits text by decreasing order of importance: Double Newlines (Paragraphs) -> Single Newlines -> Spaces.
- **Reasoning**: This preserves the semantic integrity of paragraphs and sentences. It ensures that chunks stay within the token limit (max 2000 chars) while avoiding cutting a sentence in the middle of a thought.

### 2. Embedding & Representation
- **Model**: `intfloat/multilingual-e5-large`.
- **Logic**: We use one of the highest-ranking multilingual models to generate 1024-dimensional vectors. Each chunk is transformed into a dense vector representing its legal meaning.

### 3. Vector Storage (ChromaDB)
- **Consolidation**: All document types are stored in a **single unified collection** (`legal_docs`).
- **Persistence**: The database is stored on disk in the `vectordb/` folder, meaning it doesn't need to be rebuilt every time the server restarts.

---

## Data Pipeline

The pipeline orchestrates the entire ingestion process:
1. Scans the `data/` directories.
2. Extracts text from `.docx` using `docx2txt`.
3. Applies the category-specific chunking strategy.
4. Generates embeddings in batches of 32 for memory efficiency.
5. Saves everything into ChromaDB.

*To run manually:* `python core/data_pipeline.py`

---

## API Manual

The API is built with FastAPI and pre-loads the models on startup for sub-second retrieval.

### Start the Server
```bash
python api/main.py
```
*Access the interactive docs at: http://127.0.0.1:8000/docs*

### Endpoints

#### **1. Search** (`POST /search`)
Submit a query to find the most relevant legal texts.
- **Payload**:
  ```json
  {
    "query": "USER_QUERY",
    "top_k": 5,
    "threshold": 0.7
  }
  ```
- **Response**: Returns a list of matches including the text, source file name, document type (law/judgment/fatwa), and the similarity score.

---

