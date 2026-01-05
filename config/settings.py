import os

class Settings:

    # Paths
    base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    data_path = os.path.join(base,"data")
    fatwas = os.path.join(data_path,"fatwas")
    judgments = os.path.join(data_path,"judgments")
    laws = os.path.join(data_path,"laws")
    indices_path = os.path.join(base, "vectordb/")

    # Embedding Settings
    # embedding_model = "TII-UAENLP/Arabic-E5-base"
    # embedding_model = "intfloat/multilingual-e5-small"
    embedding_model = "intfloat/multilingual-e5-large"

    # Chunking Settings
    chunk_size = 2000
    chunk_overlap = 100
    law_max_chunk_size = 2000