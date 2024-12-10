from fastapi import FastAPI
from phi.agent import Agent
from phi.model.openai import OpenAIChat
from phi.knowledge.pdf import PDFKnowledgeBase
from phi.vectordb.pgvector import PgVector, SearchType
from phi.embedder.openai import OpenAIEmbedder

from app.config import get_settings

settings = get_settings()

# Initialize FastAPI app
app = FastAPI(
    title="Knowledge Base API",
    description="API for legal matter and spend management knowledge base",
    version="1.0.0",
)

# Initialize vector database
vector_db = PgVector(
    table_name=settings.vector_db_table,
    db_url=settings.db_url,
    search_type=SearchType.hybrid,
    embedder=OpenAIEmbedder(
        model=settings.embeddings_model,
        dimensions=settings.embeddings_dimensions,
    ),
)

# Initialize knowledge base
knowledge_base = PDFKnowledgeBase(
    path="data/pdfs",  # Path to PDF documents
    vector_db=vector_db,
)

# Initialize base agent
base_agent = Agent(
    model=OpenAIChat(id="gpt-4o"),
    knowledge=knowledge_base,
    search_knowledge=True,
    read_chat_history=True,
    show_tool_calls=True,
    markdown=True,
)

@app.get("/")
async def root():
    """Root endpoint"""
    return {"message": "Knowledge Base API is running"}

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"} 