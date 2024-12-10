from typing import Optional, List, Dict, Any
import logging
from pathlib import Path
from phi.agent import Agent
from phi.llm.openai import OpenAIChat
from phi.knowledge.pdf import PDFKnowledgeBase, PDFReader
from phi.knowledge.text import TextKnowledgeBase
from phi.knowledge.combined import CombinedKnowledgeBase
from phi.vectordb.pgvector import PgVector
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
            
            # Initialize embedder (reuse the same embedder for consistency)
            embedder = OpenAIEmbedder(
                model=settings.embeddings_model,
                dimensions=settings.embeddings_dimensions,
            )
            
            # Initialize PDF knowledge base using existing table
            self.pdf_knowledge = PDFKnowledgeBase(
                path="data/pdfs",
                vector_db=PgVector(
                    table_name="pdf_documents",  # Same table as document_processor.py
                    db_url=settings.db_url,
                    embedder=embedder,
                ),
                reader=PDFReader(chunk=True),
            )
            logger.info("PDF knowledge base initialized")
            
            # Load PDF documents without recreation
            try:
                self.pdf_knowledge.load(recreate=False)
                logger.info("PDF documents loaded")
            except Exception as e:
                logger.error(f"Error loading PDF documents: {str(e)}")

            # Initialize text knowledge base using existing table
            self.text_knowledge = TextKnowledgeBase(
                path="data/text",
                vector_db=PgVector(
                    table_name="text_documents",  # Same table as document_processor.py
                    db_url=settings.db_url,
                    embedder=embedder,
                ),
            )
            logger.info("Text knowledge base initialized")
            
            # Load text documents without recreation
            try:
                self.text_knowledge.load(recreate=False)
                logger.info("Text documents loaded")
            except Exception as e:
                logger.error(f"Error loading text documents: {str(e)}")

            # Initialize combined knowledge base
            self.knowledge = CombinedKnowledgeBase(
                sources=[
                    self.pdf_knowledge,
                    self.text_knowledge,
                ],
                vector_db=PgVector(
                    table_name=settings.vector_db_table,  # Use the main table from settings
                    db_url=settings.db_url,
                    embedder=embedder,
                ),
            )
            logger.info("Combined knowledge base initialized")

            # Initialize the agent
            self.agent = Agent(
                name="Documentation Assistant",
                description="I help answer questions about documentation and manage document-related tasks.",
                llm=OpenAIChat(
                    model="gpt-4-turbo-preview",
                    temperature=0.7,
                    system_prompt=self._get_system_prompt(),
                ),
                knowledge=self.knowledge,
                show_tool_calls=True,
                search_knowledge=True,
                markdown=True,
            )
            logger.info("Agent initialized successfully")
            
        except Exception as e:
            logger.error(f"Error initializing DocumentationAgent: {str(e)}", exc_info=True)
            raise

    def _get_system_prompt(self) -> str:
        """Get the system prompt for the agent"""
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
- Focus on accuracy and clarity in responses

Format your responses in markdown for better readability."""

    async def query(self, question: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Process a documentation-related query
        
        Args:
            question: The user's question
            context: Optional context information
            
        Returns:
            Dict containing the response and any relevant metadata
        """
        try:
            logger.info(f"Processing query: {question}")
            
            # Verify knowledge bases are loaded
            if not hasattr(self, 'knowledge') or not hasattr(self, 'agent'):
                raise ValueError("Agent or knowledge base not properly initialized")
            
            # Search for relevant documents
            search_results = self.agent.search_knowledge(
                query=question,
                n_results=5
            )
            logger.info(f"Found {len(search_results) if search_results else 0} relevant documents")
            
            # Create context with search results
            context = context or {}
            context.update({
                "search_results": search_results,
                "question": question
            })
            
            # Get response from the agent using chat
            response = self.agent.chat(
                message=question,
                context=context,
            )
            logger.info("Response received from agent")

            return {
                "status": "success",
                "response": response,
                "relevant_documents": search_results,
                "metadata": {
                    "confidence": getattr(response, "confidence", 1.0),
                    "sources": getattr(response, "sources", []),
                }
            }
        except Exception as e:
            logger.error(f"Error processing query: {str(e)}", exc_info=True)
            return {
                "status": "error",
                "error": str(e),
                "message": f"Failed to process documentation query: {str(e)}"
            }

    async def search_documents(self, query: str, n_results: int = 5) -> Dict[str, Any]:
        """
        Search for relevant documents based on a query
        
        Args:
            query: Search query
            n_results: Maximum number of results to return
            
        Returns:
            Dict containing search results and metadata
        """
        try:
            logger.info(f"Searching documents with query: {query}")
            
            # Search using the agent's knowledge search
            results = self.agent.search_knowledge(
                query=query,
                n_results=n_results
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
                "error": str(e),
                "message": f"Failed to search documents: {str(e)}"
            }

    def get_stats(self) -> Dict[str, Any]:
        """Get statistics about the documentation knowledge base"""
        try:
            logger.info("Getting knowledge base statistics")
            
            # Get document counts using direct database queries
            try:
                # Count PDF documents
                if hasattr(self.pdf_knowledge.vector_db, 'engine'):
                    with self.pdf_knowledge.vector_db.engine.connect() as conn:
                        pdf_count = conn.execute(
                            sa.text(f"SELECT COUNT(*) FROM {self.pdf_knowledge.vector_db.table_name}")
                        ).scalar() or 0
                else:
                    pdf_count = 0
                    logger.warning("PDF vector database not properly initialized")
            except Exception as e:
                logger.warning(f"Could not get PDF document count: {str(e)}")
                pdf_count = 0
            
            try:
                # Count text documents
                if hasattr(self.text_knowledge.vector_db, 'engine'):
                    with self.text_knowledge.vector_db.engine.connect() as conn:
                        text_count = conn.execute(
                            sa.text(f"SELECT COUNT(*) FROM {self.text_knowledge.vector_db.table_name}")
                        ).scalar() or 0
                else:
                    text_count = 0
                    logger.warning("Text vector database not properly initialized")
            except Exception as e:
                logger.warning(f"Could not get text document count: {str(e)}")
                text_count = 0
            
            stats = {
                "status": "success",
                "stats": {
                    "total_documents": pdf_count + text_count,
                    "pdf_documents": pdf_count,
                    "text_documents": text_count,
                    "last_updated": self.agent.last_updated if hasattr(self.agent, 'last_updated') else None,
                }
            }
            logger.info(f"Statistics retrieved: {stats}")
            return stats
            
        except Exception as e:
            logger.error(f"Error getting statistics: {str(e)}", exc_info=True)
            return {
                "status": "error",
                "error": str(e),
                "message": f"Failed to get documentation stats: {str(e)}"
            } 