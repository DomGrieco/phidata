from typing import Optional, Dict, Any
import logging
from pathlib import Path
from phi.assistant import Assistant
from phi.llm.openai import OpenAIChat
from phi.knowledge.pdf import PDFKnowledgeBase, PDFReader
from phi.knowledge.text import TextKnowledgeBase
from phi.knowledge.combined import CombinedKnowledgeBase
from phi.vectordb.pgvector import PgVector
from phi.embedder.openai import OpenAIEmbedder

from app.config import get_settings

settings = get_settings()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DocumentationAgent:
    """Agent for handling documentation-related queries using Phidata's RAG capabilities"""

    def __init__(self):
        try:
            logger.info("Initializing DocumentationAgent...")
            
            # Ensure data directories exist
            Path("data/pdfs").mkdir(parents=True, exist_ok=True)
            Path("data/text").mkdir(parents=True, exist_ok=True)
            
            # Initialize embedder
            embedder = OpenAIEmbedder(
                model=settings.embeddings_model,
                dimensions=settings.embeddings_dimensions,
            )
            
            # Initialize knowledge bases
            self.pdf_knowledge = PDFKnowledgeBase(
                path="data/pdfs",
                vector_db=PgVector(
                    table_name="pdf_documents",
                    db_url=settings.db_url,
                    embedder=embedder
                ),
                reader=PDFReader(chunk=True),
            )
            logger.info("PDF knowledge base initialized")
            
            self.text_knowledge = TextKnowledgeBase(
                path="data/text",
                vector_db=PgVector(
                    table_name="text_documents",
                    db_url=settings.db_url,
                    embedder=embedder
                ),
            )
            logger.info("Text knowledge base initialized")
            
            # Load knowledge bases
            self.pdf_knowledge.load(recreate=False)
            self.text_knowledge.load(recreate=False)
            
            # Initialize combined knowledge base
            self.knowledge = CombinedKnowledgeBase(
                sources=[self.pdf_knowledge, self.text_knowledge],
                vector_db=PgVector(
                    table_name=settings.vector_db_table,
                    db_url=settings.db_url,
                    embedder=embedder
                ),
            )
            self.knowledge.load(recreate=False)
            logger.info("Combined knowledge base initialized")

            # Initialize the assistant with RAG capabilities
            self.assistant = Assistant(
                name="Documentation Assistant",
                description="I help answer questions about documentation using the knowledge base.",
                llm=OpenAIChat(
                    model="gpt-4o-mini",
                    temperature=0.1,
                    system_prompt=self._get_system_prompt(),
                ),
                knowledge_base=self.knowledge,
                show_references=True,
            )
            logger.info("Assistant initialized successfully")
            
        except Exception as e:
            logger.error(f"Error initializing DocumentationAgent: {str(e)}", exc_info=True)
            raise

    def _get_system_prompt(self) -> str:
        """Get the system prompt for the assistant"""
        return """You are a documentation assistant. Answer the following question using ONLY the provided documentation context.
If the exact information is found in the documentation, use it directly and precisely.
If you're not sure or the information isn't explicitly stated in the provided context, say so.
Do not make assumptions or add information not present in the documentation."""

    def query(self, question: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Process a documentation-related query using Phidata's RAG"""
        try:
            logger.info(f"Processing query: {question}")
            
            if not hasattr(self, 'knowledge') or not hasattr(self, 'assistant'):
                raise ValueError("Assistant or knowledge base not properly initialized")
            
            # Let Phidata handle the RAG process
            response = self.assistant.run(
                message=question,
                context=context or {},
            )
            
            # Process response
            response_text = []
            for chunk in response:
                if isinstance(chunk, str):
                    response_text.append(chunk)
                elif isinstance(chunk, dict) and "content" in chunk:
                    response_text.append(chunk["content"])
                elif hasattr(chunk, "content"):
                    response_text.append(chunk.content)
            
            final_response = "".join(response_text)
            logger.info("Response received from assistant")

            return {
                "status": "success",
                "response": final_response,
                "metadata": {
                    "sources": getattr(response, "sources", [])
                }
            }
            
        except Exception as e:
            logger.error(f"Error processing query: {str(e)}", exc_info=True)
            return {
                "status": "error",
                "message": f"Failed to process documentation query: {str(e)}"
            }

    def get_stats(self) -> Dict[str, Any]:
        """Get statistics about the documentation knowledge base"""
        try:
            logger.info("Getting knowledge base statistics")
            
            # Use simple search to count documents
            pdf_count = len(self.pdf_knowledge.vector_db.search("*"))
            text_count = len(self.text_knowledge.vector_db.search("*"))
            
            stats = {
                "status": "success",
                "stats": {
                    "total_documents": pdf_count + text_count,
                    "pdf_documents": pdf_count,
                    "text_documents": text_count,
                }
            }
            logger.info(f"Statistics retrieved: {stats}")
            return stats
            
        except Exception as e:
            logger.error(f"Error getting statistics: {str(e)}", exc_info=True)
            return {
                "status": "error",
                "message": f"Failed to get statistics: {str(e)}"
            } 