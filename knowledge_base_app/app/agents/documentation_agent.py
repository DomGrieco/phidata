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
            
            # Initialize PDF knowledge base
            self.pdf_knowledge = PDFKnowledgeBase(
                path="data/pdfs",
                vector_db=PgVector(
                    table_name="pdf_documents",
                    db_url=settings.db_url,
                    embedder=embedder
                ),
                reader=PDFReader(
                    chunk=True,
                    chunk_size=500,
                    chunk_overlap=50
                ),
            )
            logger.info("PDF knowledge base initialized")
            
            # Initialize text knowledge base
            self.text_knowledge = TextKnowledgeBase(
                path="data/text",
                vector_db=PgVector(
                    table_name="text_documents",
                    db_url=settings.db_url,
                    embedder=embedder
                ),
                chunk=True,          # Enable chunking for text documents
                chunk_size=500,      # Consistent with PDF chunking
                chunk_overlap=50     # Maintain context between chunks
            )
            logger.info("Text knowledge base initialized")
            
            # Load knowledge bases with recreate to apply chunking settings
            logger.info("Loading knowledge bases with new chunking settings...")
            self.pdf_knowledge.load(recreate=False)  # Recreate to apply new chunking
            self.text_knowledge.load(recreate=False)  # Recreate to apply new chunking
            
            # Initialize combined knowledge base
            self.knowledge = CombinedKnowledgeBase(
                sources=[self.pdf_knowledge, self.text_knowledge],
                vector_db=PgVector(
                    table_name=settings.vector_db_table,
                    db_url=settings.db_url,
                    embedder=embedder
                ),
            )
            self.knowledge.load(recreate=False)  # Recreate to ensure proper combination
            logger.info("Combined knowledge base initialized")

            # Initialize the assistant with RAG-specific configuration
            self.assistant = Assistant(
                name="Documentation Assistant",
                description="I help answer questions using the provided documentation knowledge base.",
                llm=OpenAIChat(
                    model="gpt-4o-mini",
                    temperature=0.2,
                    system_prompt=self._get_system_prompt(),
                ),
                knowledge_base=self.knowledge,
                show_references=True,
                search_knowledge=True,  # Explicitly enable knowledge base usage
            )
            logger.info("Assistant initialized successfully")
            
        except Exception as e:
            logger.error(f"Error initializing DocumentationAgent: {str(e)}", exc_info=True)
            raise

    def _get_system_prompt(self) -> str:
        """Get the system prompt for the assistant"""
        return """You are a documentation assistant with access to a knowledge base of documentation.
IMPORTANT: You MUST use the provided knowledge base to answer questions.

When answering:
1. ONLY use information from the provided knowledge base documents
2. ALWAYS cite the specific documents you reference
3. If you can't find relevant information in the knowledge base, say so clearly
4. DO NOT make assumptions or add information not present in the documents

For each response:
- Start by searching the knowledge base
- Quote relevant sections directly when possible
- Include document references
- If information is missing or unclear, say "I cannot find specific information about this in the documentation"

Remember: Your responses must be based SOLELY on the provided documentation."""

    def query(self, question: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Process a documentation-related query using Phidata's RAG"""
        try:
            logger.info(f"Processing query: {question}")
            
            if not hasattr(self, 'knowledge') or not hasattr(self, 'assistant'):
                raise ValueError("Assistant or knowledge base not properly initialized")
            
            # Search for relevant documents
            relevant_docs = self.knowledge.search(query=question)
            logger.info(f"Found {len(relevant_docs)} potentially relevant documents")
            
            # Create RAG-specific context
            rag_context = {
                **(context or {}),
                "require_knowledge_base": True,
                "max_sources": 5,
            }
            
            # Let Phidata handle the RAG process
            response = self.assistant.run(
                message=question,
                context=rag_context,
                knowledge_base=relevant_docs
            )
            
            # Process response and track sources
            response_text = []
            sources = []
            
            # Process the response and collect sources
            if isinstance(response, str):
                response_text.append(response)
            else:
                try:
                    # Handle generator or iterable response
                    for chunk in response:
                        if isinstance(chunk, str):
                            response_text.append(chunk)
                        elif isinstance(chunk, dict):
                            if "content" in chunk:
                                response_text.append(chunk["content"])
                            if "sources" in chunk:
                                sources.extend(chunk["sources"])
                        elif hasattr(chunk, "content"):
                            response_text.append(chunk.content)
                            if hasattr(chunk, "sources"):
                                sources.extend(chunk.sources)
                except Exception as e:
                    logger.warning(f"Error processing response chunk: {str(e)}")
            
            final_response = "".join(response_text)
            
            # If we found relevant docs but no sources are tracked, use the relevant docs as sources
            if not sources and relevant_docs:
                sources = relevant_docs[:5]  # Use top 5 relevant docs as sources
                logger.info("Using relevant docs as sources since no sources were explicitly tracked")
            
            logger.info(f"Response generated using {len(sources)} source documents")
            
            return {
                "status": "success",
                "response": final_response,
                "metadata": {
                    "sources": sources,
                    "total_relevant_docs": len(relevant_docs),
                    "used_docs": len(sources),
                    "has_sources": bool(sources)
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