"""
PDF Parser
Extracts and chunks content from PDF documents for vector search.
"""
from pathlib import Path
from typing import List, Dict, Optional
import re
from dataclasses import dataclass

try:
    import pdfplumber
    import PyPDF2
except ImportError:
    pdfplumber = None
    PyPDF2 = None


@dataclass
class PDFChunk:
    """A chunk of text from a PDF document."""
    text: str
    page_number: int
    chunk_id: int
    metadata: Dict


class PDFParser:
    """Parser for PDF documents."""
    
    def __init__(self, chunk_size: int = 1000, chunk_overlap: int = 200):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
    
    def parse(self, pdf_path: Path) -> List[PDFChunk]:
        """Parse a PDF file and extract chunks."""
        if not pdfplumber:
            raise ImportError("pdfplumber not installed")
        
        chunks = []
        chunk_id = 0
        
        with pdfplumber.open(pdf_path) as pdf:
            for page_num, page in enumerate(pdf.pages, start=1):
                text = page.extract_text()
                
                if not text:
                    continue
                
                # Clean text
                text = self._clean_text(text)
                
                # Split into chunks
                page_chunks = self._chunk_text(text, page_num, chunk_id)
                chunks.extend(page_chunks)
                chunk_id += len(page_chunks)
        
        return chunks
    
    def _clean_text(self, text: str) -> str:
        """Clean extracted text."""
        # Remove excessive whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Remove page numbers and headers/footers (heuristic)
        text = re.sub(r'^\d+\s*$', '', text, flags=re.MULTILINE)
        
        return text.strip()
    
    def _chunk_text(self, text: str, page_num: int, start_id: int) -> List[PDFChunk]:
        """Split text into overlapping chunks."""
        chunks = []
        
        # Split by sentences
        sentences = re.split(r'(?<=[.!?])\s+', text)
        
        current_chunk = []
        current_length = 0
        chunk_id = start_id
        
        for sentence in sentences:
            sentence_length = len(sentence)
            
            if current_length + sentence_length > self.chunk_size and current_chunk:
                # Create chunk
                chunk_text = ' '.join(current_chunk)
                chunks.append(PDFChunk(
                    text=chunk_text,
                    page_number=page_num,
                    chunk_id=chunk_id,
                    metadata={"source": "pdf", "page": page_num}
                ))
                
                # Keep overlap
                overlap_sentences = []
                overlap_length = 0
                for s in reversed(current_chunk):
                    if overlap_length + len(s) <= self.chunk_overlap:
                        overlap_sentences.insert(0, s)
                        overlap_length += len(s)
                    else:
                        break
                
                current_chunk = overlap_sentences
                current_length = overlap_length
                chunk_id += 1
            
            current_chunk.append(sentence)
            current_length += sentence_length
        
        # Add remaining
        if current_chunk:
            chunk_text = ' '.join(current_chunk)
            chunks.append(PDFChunk(
                text=chunk_text,
                page_number=page_num,
                chunk_id=chunk_id,
                metadata={"source": "pdf", "page": page_num}
            ))
        
        return chunks
    
    def extract_metadata(self, pdf_path: Path) -> Dict:
        """Extract PDF metadata."""
        if not PyPDF2:
            return {}
        
        metadata = {}
        
        try:
            with open(pdf_path, 'rb') as file:
                reader = PyPDF2.PdfReader(file)
                info = reader.metadata
                
                if info:
                    metadata = {
                        "title": info.get("/Title", ""),
                        "author": info.get("/Author", ""),
                        "subject": info.get("/Subject", ""),
                        "creator": info.get("/Creator", ""),
                        "pages": len(reader.pages)
                    }
        except Exception:
            pass
        
        return metadata
