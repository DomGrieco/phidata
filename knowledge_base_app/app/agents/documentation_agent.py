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
        return """You are a knowledgeable assistant specialized in handling documentation-related queries.
Your primary responsibilities include:

1. Answering questions about documents in the knowledge base, refrain from making up information not found in the documents
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

    def extract_document_info(self, doc: Any) -> Dict[str, Any]:
        """Extract clean document information from various formats"""
        try:
            # If it's a string, try to extract content
            if isinstance(doc, str):
                # Extract content between content=' and the next space
                if "content='" in doc:
                    content_start = doc.find("content='") + 9
                    content_end = doc.find("'", content_start)
                    if content_end != -1:
                        content = doc[content_start:content_end]
                        # Split content to get document name and section
                        parts = content.split(" ", 2)
                        if len(parts) >= 2:
                            return {
                                "name": parts[0],
                                "section": parts[1] if len(parts) > 1 else "General"
                            }
                return {"name": "Unknown Document", "section": "General"}
            
            # If it's a dictionary, extract relevant fields
            elif isinstance(doc, dict):
                return {
                    "name": doc.get("name", doc.get("file_name", "Unknown Document")),
                    "section": doc.get("section", "General"),
                    "page": doc.get("page", None)
                }
            
            return {"name": str(doc)[:50], "section": "General"}
            
        except Exception as e:
            logger.warning(f"Error extracting document info: {str(e)}")
            return {"name": "Unknown Document", "section": "General"}

    def query(self, question: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Process a documentation-related query"""
        try:
            logger.info(f"Processing query: {question}")
            
            if not hasattr(self, 'knowledge') or not hasattr(self, 'assistant'):
                raise ValueError("Assistant or knowledge base not properly initialized")
            
            # Search for relevant documents
            search_results = self.knowledge.search(query=question)
            logger.info(f"Found {len(search_results) if search_results else 0} relevant documents")
            
            # Clean document information before processing
            clean_results = []
            for doc in search_results:
                clean_doc = self.extract_document_info(doc)
                if clean_doc:
                    clean_results.append(clean_doc)
            
            # Get response from assistant
            response_gen = self.assistant.run(
                message=question,
                context=context or {},
                knowledge_base=search_results  # Use original results for context
            )
            
            # Process response chunks efficiently
            response_text = []
            for chunk in response_gen:
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
                "relevant_documents": clean_results,  # Use clean results for display
                "metadata": {
                    "source_count": len(clean_results)
                }
            }
            
        except Exception as e:
            logger.error(f"Error processing query: {str(e)}", exc_info=True)
            return {
                "status": "error",
                "message": f"Failed to process documentation query: {str(e)}"
            }

    def search_documents(self, query: str, limit: int = 2) -> Dict[str, Any]:
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