from typing import Optional, List, Dict, Any
import logging
from pathlib import Path
from phi.assistant import Assistant
from phi.llm.openai import OpenAIChat
from phi.knowledge.pdf import PDFKnowledgeBase, PDFReader
from phi.knowledge.text import TextKnowledgeBase
from phi.knowledge.combined import CombinedKnowledgeBase
from phi.vectordb.pgvector import PgVector, SearchType
from phi.embedder.openai import OpenAIEmbedder
import sqlalchemy as sa

from app.config import get_settings

settings = get_settings()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DocumentationAgent:
    """Agent for handling documentation-related queries and tasks"""

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
                    embedder=embedder,
                    search_type=SearchType.hybrid,
                ),
                reader=PDFReader(chunk=True),
            )
            logger.info("PDF knowledge base initialized")
            
            # Load PDF documents (this will create the table if it doesn't exist)
            self.pdf_knowledge.load(recreate=False)
            logger.info("PDF documents loaded")

            # Initialize text knowledge base
            self.text_knowledge = TextKnowledgeBase(
                path="data/text",
                vector_db=PgVector(
                    table_name="text_documents",
                    db_url=settings.db_url,
                    embedder=embedder,
                    search_type=SearchType.hybrid,
                ),
            )
            logger.info("Text knowledge base initialized")
            
            # Load text documents (this will create the table if it doesn't exist)
            self.text_knowledge.load(recreate=False)
            logger.info("Text documents loaded")

            # Initialize combined knowledge base
            self.knowledge = CombinedKnowledgeBase(
                sources=[self.pdf_knowledge, self.text_knowledge],
                vector_db=PgVector(
                    table_name=settings.vector_db_table,
                    db_url=settings.db_url,
                    embedder=embedder,
                    search_type=SearchType.hybrid,
                ),
            )
            # Load combined knowledge base (this will create the table if it doesn't exist)
            self.knowledge.load(recreate=False)
            logger.info("Combined knowledge base initialized")

            # Initialize the assistant
            self.assistant = Assistant(
                name="Documentation Assistant",
                description="I help answer questions about documentation and manage document-related tasks.",
                llm=OpenAIChat(
                    model="gpt-4o",
                    temperature=0.7,
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
        return """You are a knowledgeable assistant specialized in handling documentation-related queries.
Your primary responsibilities include:

1. Answering questions about documents in the knowledge base
2. Providing relevant context and citations from documents
3. Identifying gaps or inconsistencies in documentation
4. Suggesting documentation updates when necessary
5. Maintaining version awareness of documents

Guidelines:
- Always provide specific references to documents you're citing
- If information is ambiguous or unclear, ask for clarification
- When suggesting updates, explain the rationale
- Maintain awareness of document versions and relevance

Format your responses in markdown for better readability."""

    def query(self, question: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Process a documentation-related query"""
        try:
            logger.info(f"Processing query: {question}")
            
            if not hasattr(self, 'knowledge') or not hasattr(self, 'assistant'):
                raise ValueError("Assistant or knowledge base not properly initialized")
            
            # Search for relevant documents using the correct search method
            search_results = self.knowledge.search(query=question)
            logger.info(f"Found {len(search_results) if search_results else 0} relevant documents")
            
            # Get response from assistant and convert generator to string
            response_gen = self.assistant.run(
                message=question,
                context=context or {},
                knowledge_base=search_results
            )
            
            # Convert generator to string
            response_text = ""
            try:
                for chunk in response_gen:
                    if isinstance(chunk, str):
                        response_text += chunk
                    elif isinstance(chunk, dict) and "content" in chunk:
                        response_text += chunk["content"]
                    elif hasattr(chunk, "content"):
                        response_text += chunk.content
            except Exception as e:
                logger.error(f"Error processing response chunks: {str(e)}")
                raise
                
            logger.info("Response received from assistant")

            return {
                "status": "success",
                "response": response_text,
                "relevant_documents": search_results,
                "metadata": {
                    "sources": getattr(response_gen, "sources", []),
                }
            }
        except Exception as e:
            logger.error(f"Error processing query: {str(e)}", exc_info=True)
            return {
                "status": "error",
                "message": f"Failed to process documentation query: {str(e)}"
            }

    def search_documents(self, query: str, limit: int = 5) -> Dict[str, Any]:
        """Search for relevant documents based on a query"""
        try:
            logger.info(f"Searching documents with query: {query}")
            
            # Use the vector_db directly for searching with limit
            results = self.knowledge.vector_db.search(
                query=query,
                limit=limit
            )
            result_count = len(results) if results else 0
            logger.info(f"Found {result_count} search results")
            
            return {
                "status": "success",
                "results": results,
                "metadata": {
                    "total_results": result_count,
                    "query": query,
                }
            }
        except Exception as e:
            logger.error(f"Error searching documents: {str(e)}", exc_info=True)
            return {
                "status": "error",
                "message": f"Failed to search documents: {str(e)}"
            }

    def get_stats(self) -> Dict[str, Any]:
        """Get statistics about the documentation knowledge base"""
        try:
            logger.info("Getting knowledge base statistics")
            
            # Get document counts using vector_db directly
            try:
                pdf_count = len(self.pdf_knowledge.vector_db.search(query="*")) if hasattr(self, 'pdf_knowledge') else 0
            except Exception as e:
                logger.warning(f"Could not get PDF document count: {str(e)}")
                pdf_count = 0
                
            try:
                text_count = len(self.text_knowledge.vector_db.search(query="*")) if hasattr(self, 'text_knowledge') else 0
            except Exception as e:
                logger.warning(f"Could not get text document count: {str(e)}")
                text_count = 0
            
            stats = {
                "status": "success",
                "stats": {
                    "total_documents": pdf_count + text_count,
                    "pdf_documents": pdf_count,
                    "text_documents": text_count,
                    "last_updated": None,  # We'll implement this later if needed
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