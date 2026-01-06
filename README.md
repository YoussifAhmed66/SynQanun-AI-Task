# SynQanun: Arabic Legal Semantic Search Engine

SynQanun is a high-performance semantic search pipeline designed specifically for Arabic legal documents, including Laws, Judgments, and Fatwas. 

## Overview

The system transforms raw `.docx` legal documents into a searchable vector database. It uses the state-of-the-art **BAAI/bge-m3** multilingual model to understand the *meaning* behind legal queries rather than just matching keywords.

---

## Directory Structure

```text
SynQanun-AI-Task/
├── api/
│   └── main.py          # FastAPI application & endpoints
├── config/
│   └── settings.py       # Centralized configuration (paths, model, chunking)
├── core/
│   ├── chunker.py       # Custom logic for Laws and Narrative documents
│   ├── embedder.py      # Sentence-Transformers wrapper
│   ├── search_engine.py  # Hierarchical Document-Level Aggregation interface
│   └── vector_store.py  # ChromaDB management
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
- **Reasoning**: Legal laws are inherently organized by Articles. An Article is a complete semantic unit of a legal rule. By chunking exactly at Article boundaries, we ensure that a user retrieving a rule gets the *entire* context of that specific article.
- **Safety**: If an article is exceptionally long, the system automatically triggers a recursive split to ensure the embedding model remains effective.

#### **Judgments & Fatwas (Recursive Character Splitting)**
- **Method**: Narrative documents use a **Recursive Character Splitter** that splits text by Paragraphs -> Newlines -> Spaces.
- **Reasoning**: This preserves the semantic integrity of blocks of text, ensuring that chunks stay within the efficient token limit while avoiding mid-sentence cuts.

### 2. Embedding & Representation
- **Model**: `BAAI/bge-m3`.
- **Logic**: We use one of the highest-ranking multilingual models to generate dense 1024-dimensional vectors. This model is specifically strong at retrieving Arabic semantic meaning.

### 3. Document-Level Aggregation
- **Method**: While search operates at the chunk level for precision, results are aggregated by **source document**.
- **Reasoning**: The system groups multiple matching chunks into a hierarchical document-level result, showing which document is most relevant and providing the specific snippets that triggered the match.

### 4. Vector Storage (ChromaDB)
- **Consolidation**: All document types are stored in a unified collection (`legal_docs`).
- **Persistence**: The database is stored on disk in the `vectordb/` folder for persistence.

---

## Data Pipeline

The pipeline orchestrates the entire ingestion process:
1. Scans the `data/` directories.
2. Extracts text from `.docx` using `docx2txt`.
3. Applies the category-specific chunking strategy.
4. Generates embeddings in batches for efficiency.
5. Saves everything into ChromaDB.

*To run manually:* `python core/data_pipeline.py`

---

## API Manual

### Endpoints

### **Search Endpoint** (`POST /search`)
Submit a query to find the most relevant legal texts.
- **Parameters**:
  - `question`: Search query (Arabic text).
  - `top_k`: Number of results to return.
  - `threshold`: Minimum similarity score (Default: 0.6). Used to filter out low-relevance results and ensure only semantically similar documents are returned.
- **Request Body**:
  ```json
  {
    "question": "هل تسقط حقوق الموظف في المعاش لو اتحكم عليه في جريمة رشوة؟",
    "top_k": 5,
    "threshold": 0.6
  }
  ```
- **Response**: Returns a list of document-level matches including the source, type, and the matching chunks within that document.

---

## Example Output
```json
{
  "question": "هل تسقط حقوق الموظف في المعاش لو اتحكم عليه في جريمة رشوة؟",
  "results": [
    {
      "source": "fatwa1_1960.docx",
      "type": "fatwas",
      "max_score": 0.6321662664413452,
      "chunks": [
        {
          "text": "جمهورية مصر العربية - الفتوى رقم 99 لسنة 1960 بتاريخ 1960-01-30 تاريخ الجلسة 1960-01-13\n\n\n\nمبدأ 1\n\nالتنفيذ على المعاش\nمعاش ـ الخصم منه ـ الغرامة المحكوم بها على صاحب المعاش فى إحدى الجرائم المنصوص عليها فى الفقرة (1) من المادة (56) من القانون رقم (37) لسنة 1929 فى شأن المعاشات الملكية ـ جواز تحصيل قيمتها بطريق الخصم من المعاش الممنوح للمستحقين عنه فى حدود الربع ـ أساس ذلك.\nتنص المادة (56) من القانون رقم (37) لسنة 1929 فى شأن المعاشات الملكية على أن: \"كل موظف أو مستخدم أو صاحب معاش صدر عليه حكم فى جريمة غدر أو إختلاس أموال الحكومة أو رشوة أو تزوير فى أوراق رسمية تسقط حقوقه فى المعاش أو المكافأة ولو بعد قيد المعاش أو تسوية المكافأة، وفى هذه الحالة إذا كان يوجد أشخاص يستحقون معاشاً أو مكافأة عند وفاة الموظف أو المستخدم أو صاحب المعاش يمنحون نصف جزء المعاش أو المكافأة الذى كانوا يستحقونه فيما لو توفى عائلهم. فاذا كان الموظف أو المستخدم أو صاحب المعاش المحكوم عليه فى إحدى الجرائم المنصوص عليها فى الفقرة السابقة مديناً للحكومة من جراء ارتكابه الأفعال المكونة للجريمة، يخصم من المعاش أو المكافأة الممنوحة للمستحقين عنه جزء حتى وفاء الدين، ولا يجوز فى حال من الأحوال أن يتجاوز هذا الاستقطاع ربع المعاش أو المكافأة\". ويؤخذ من هذا النص أن المشرع أجاز الخصم فى حدود الربع من المعاش أو المكافأة الممنوحة للمستحقين عن الموظف أوالمستخدم أو صاحب معاش المحكوم عليه فى إحدى الجرائم المنصوص عليها فى الفقرة الأولى منها ـ ومنها جريمة الرشوة ـ وذلك وفاء لما يكون المحكوم عليه مدينا به للحكومة من جراء ارتكابه الأفعال المكونة للجريمة.\nولما كانت المادة (22) من قانون العقوبات قد عرفت عقوبة الغرامة بأنها الزام المحكوم عليه بأن يدفع إلى خزينة الحكومة المبلغ المقدر فى الحكم، وظاهر من هذا التعريف أن الغرامة عقوبة ذات طابع مالى، تتمثل فى مبلغ من المال يقدره الحكم الصادر بها، وهى وأن كانت جزاء جنائيا يقصد به الإيلام مجرداً من كل معنى من معانى التعويض، إلا أنها تصبح بمجرد الحكم النهائى بها دينا للحكومة فى ذمة المحكوم عليه ـ شأنها فى ذلك شأن التعويض ـ ومن ثم يجوز التنفيذ بها على امواله وعلى تركته بعد وفاته.",
          "score": 0.6321662664413452,
          "metadata": {
            "id": "chunk_1",
            "chunk_type": "recursive"
          }
        },
        {
          "text": "الرأى\n\nانتهى الرأى إلى جواز تحصيل قيمة الغرامة المحكوم بها على صاحب المعاش ـ فى جريمة رشوة ـ بطريق الخصم من المعاش الممنوح للمستحقين عنه ـ فى حدود الربع ـ تطبيقاً للمادة (56) من القانون رقم (37) لسنة 1929 فى شأن المعاشات الملكية.",
          "score": 0.6173504590988159,
          "metadata": {
            "chunk_type": "recursive",
            "id": "chunk_3"
          }
        }
      ]
    }
  ]
}
```

---

## Limitations
- **First-Run Latency**: Initial loading of the `bge-m3` weights may take a few seconds on first request.
- **Granularity**: The current article-based chunking for laws is highly specialized for Article-structured text and may need adjustment for laws with different naming conventions.
- **Aggregation Strategy**: Document ranking currently prioritizes the single most relevant chunk not the whole document (Max-Pooling).
