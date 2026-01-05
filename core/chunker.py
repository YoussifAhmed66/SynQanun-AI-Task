import re
import os
import sys

# Ensure we can import from project root
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.load_docx import check_file
from config.settings import Settings

class Chunker:
    def __init__(self):
        pass

    def _recursive_split(self, text, chunk_size=Settings.chunk_size, overlap=Settings.chunk_overlap, separators=None):
        """
        Helper for recursive character splitting.
        """
        if separators is None:
            separators = ["\n\n", "\n", " ", ""]
            
        final_chunks = []
        if not separators:
            return [text]
        
        sep = separators[0]
        if sep == "":
            split_text = list(text) # Base case: split by char
        else:
            split_text = text.split(sep)
            
        current_chunk = []
        current_len = 0
        
        for segment in split_text:
            segment_len = len(segment)
            if sep != "":
                segment_len += len(sep) # Count separator length approx
            
            if current_len + segment_len > chunk_size and current_chunk:
                # Join current buffer
                joined = sep.join(current_chunk) if sep != "" else "".join(current_chunk)
                final_chunks.append(joined)
                
                # Handle Overlap: Keep last few segments that fit within overlap
                overlap_len = 0
                overlap_buffer = []
                for s in reversed(current_chunk):
                    if overlap_len + len(s) < overlap:
                        overlap_buffer.insert(0, s)
                        overlap_len += len(s)
                    else:
                        break
                current_chunk = overlap_buffer
                current_len = overlap_len
            
            current_chunk.append(segment)
            current_len += segment_len
            
        # leftovers
        if current_chunk:
            joined = sep.join(current_chunk) if sep != "" else "".join(current_chunk)
            final_chunks.append(joined)
            
        # Recurse on remaining large chunks
        post_processed = []
        for c in final_chunks:
            if len(c) > chunk_size and len(separators) > 1:
                    post_processed.extend(self._recursive_split(c, chunk_size, overlap, separators[1:]))
            else:
                post_processed.append(c)
        
        return post_processed

    def chunk_law(self, text, file_name):
        """
        Separate each article and add each one to a separate chunk
        """
        chunks = []
        
        # Regex to find "Article X"
        patterns = r"(?:^|\n)(المادة\s+\d+[:\.]?)"
        parts = re.split(patterns, text)
        
        # Handle Preamble
        if parts[0].strip():
             chunks.append({
                "text": parts[0].strip(),
                "metadata": {
                    "source": file_name,
                    "type": "law",
                    "chunk_type": "preamble",
                    "id": "intro"
                }
            })

        # Handle Articles
        for i in range(1, len(parts), 2):
            header = parts[i].strip()       # "المادة 1"
            content = parts[i+1].strip() if i+1 < len(parts) else ""
            full_text = f"{header}\n{content}".strip()
            
            if full_text:
                chunks.append({
                    "text": full_text,
                    "metadata": {
                        "source": file_name,
                        "type": "law",
                        "chunk_type": "article",
                        "id": header
                    }
                })
        
        # Split oversized chunks with recursive character splitting
        final_chunks = []
        MAX_SIZE = Settings.law_max_chunk_size 
        
        for c in chunks:
            if len(c['text']) > MAX_SIZE:
                # Split huge chunk
                sub_texts = self._recursive_split(c['text'], chunk_size=Settings.chunk_size, overlap=Settings.chunk_overlap)
                for j, sub in enumerate(sub_texts):
                    new_c = {
                        "text": sub,
                        "metadata": c['metadata'].copy()
                    }
                    new_c['metadata']['id'] = f"{c['metadata']['id']}_part{j+1}"
                    new_c['metadata']['chunk_type'] = f"{c['metadata']['chunk_type']}_split"
                    final_chunks.append(new_c)
            else:
                final_chunks.append(c)
                
        return final_chunks

    def chunk_recursive(self, text, file_name, doc_type="judgment", chunk_size=Settings.chunk_size, overlap=Settings.chunk_overlap):
        """
        Chunks judgments and fatwas using recursive character splitting.
        """
        chunks = []
        
        raw_chunks = self._recursive_split(text, chunk_size, overlap)
        

        for i, rc in enumerate(raw_chunks):
            chunks.append({
                "text": rc.strip(),
                "metadata": {
                    "source": file_name,
                    "type": doc_type,
                    "chunk_type": "recursive",
                    "id": f"chunk_{i}"
                }
            })
                
        return chunks

