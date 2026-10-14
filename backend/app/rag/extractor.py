import os
import hashlib
from typing import List, Dict, Any, Tuple
import fitz  # PyMuPDF


class PDFExtractor:
    @staticmethod
    def extract_text_with_pages(file_path: str) -> List[Dict[str, Any]]:
        """
        Extract text page-by-page from a PDF file.
        Returns a list of dicts: [{'page_number': 1, 'text': '...'}]
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"PDF file not found at: {file_path}")

        pages_data = []
        doc = fitz.open(file_path)
        try:
            for page_index in range(len(doc)):
                page = doc.load_page(page_index)
                page_text = page.get_text("text").strip()
                if page_text:
                    pages_data.append({
                        "page_number": page_index + 1,
                        "text": page_text
                    })
        finally:
            doc.close()

        return pages_data

    @staticmethod
    def calculate_file_hash(file_path: str) -> str:
        """Calculate SHA-256 hash of a file for versioning and duplicate detection."""
        hasher = hashlib.sha256()
        with open(file_path, "rb") as f:
            while chunk := f.read(8192):
                hasher.update(chunk)
        return hasher.hexdigest()


class TextSplitter:
    @staticmethod
    def split_into_chunks(
        pages_data: List[Dict[str, Any]],
        chunk_size: int = 1000,
        chunk_overlap: int = 150
    ) -> List[Dict[str, Any]]:
        """
        Split page-annotated text into overlapping chunks, preserving page numbers.
        """
        chunks = []
        chunk_index = 0

        for page in pages_data:
            page_num = page["page_number"]
            text = page["text"]

            if len(text) <= chunk_size:
                chunks.append({
                    "chunk_index": chunk_index,
                    "text": text,
                    "page_number": page_num
                })
                chunk_index += 1
                continue

            # Sliding window over page text
            start = 0
            while start < len(text):
                end = start + chunk_size
                chunk_text = text[start:end].strip()
                if chunk_text:
                    chunks.append({
                        "chunk_index": chunk_index,
                        "text": chunk_text,
                        "page_number": page_num
                    })
                    chunk_index += 1
                start += (chunk_size - chunk_overlap)

        return chunks
