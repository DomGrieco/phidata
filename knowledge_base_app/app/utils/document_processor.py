from typing import List, Dict, Any
from pathlib import Path
from phi.knowledge.pdf import PDFKnowledgeBase, PDFReader
from phi.knowledge.text import TextKnowledgeBase
from phi.vectordb.pgvector import PgVector
from phi.embedder.openai import OpenAIEmbedder

from app.config import get_settings

settings = get_settings()

class DocumentProcessor:
    """Document processor for ingesting various document types into the knowledge base"""

    def __init__(self, vector_db: PgVector):
        self.vector_db = vector_db
        
        # Initialize PDF knowledge base
        self.pdf_knowledge = PDFKnowledgeBase(
            path="data/pdfs",
            vector_db=PgVector(
                table_name="pdf_documents",
                db_url=settings.db_url,
                embedder=OpenAIEmbedder(
                    model=settings.embeddings_model,
                    dimensions=settings.embeddings_dimensions,
                ),
            ),
            reader=PDFReader(chunk=True),
        )
        
        # Initialize text knowledge base
        self.text_knowledge = TextKnowledgeBase(
            path="data/text",
            vector_db=PgVector(
                table_name="text_documents",
                db_url=settings.db_url,
                embedder=OpenAIEmbedder(
                    model=settings.embeddings_model,
                    dimensions=settings.embeddings_dimensions,
                ),
            ),
        )
    
    def ingest_pdfs(self, path: str = "data/pdfs") -> Dict[str, Any]:
        """Ingest PDF documents from the specified path"""
        try:
            # Create directory if it doesn't exist
            Path(path).mkdir(parents=True, exist_ok=True)
            
            # Load PDFs into knowledge base
            self.pdf_knowledge.load(recreate=False)
            return {"status": "success", "message": f"PDFs ingested from {path}"}
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    def ingest_text(self, path: str = "data/text") -> Dict[str, Any]:
        """Ingest text documents from the specified path"""
        try:
            # Create directory if it doesn't exist
            Path(path).mkdir(parents=True, exist_ok=True)
            
            # Load text documents into knowledge base
            self.text_knowledge.load(recreate=False)
            return {"status": "success", "message": f"Text documents ingested from {path}"}
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    def get_document_count(self) -> Dict[str, int]:
        """Get total number of documents in each knowledge base"""
        try:
            pdf_count = len(self.pdf_knowledge.get_all_documents()) if hasattr(self.pdf_knowledge, 'get_all_documents') else 0
            text_count = len(self.text_knowledge.get_all_documents()) if hasattr(self.text_knowledge, 'get_all_documents') else 0
            
            return {
                "pdf_documents": pdf_count,
                "text_documents": text_count,
                "total": pdf_count + text_count
            }
        except Exception as e:
            return {
                "pdf_documents": 0,
                "text_documents": 0,
                "total": 0
            }
    
    def clear_knowledge_base(self) -> Dict[str, Any]:
        """Clear all documents from the knowledge bases"""
        try:
            self.pdf_knowledge.vector_db.delete_all()
            self.text_knowledge.vector_db.delete_all()
            return {"status": "success", "message": "Knowledge bases cleared"}
        except Exception as e:
            return {"status": "error", "message": str(e)} 