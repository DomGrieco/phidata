from typing import Optional, List
from datetime import datetime
from phi.agent import Agent
from phi.knowledge.pdf import PDFUrlKnowledgeBase
from phi.knowledge.website import WebsiteKnowledgeBase 
from phi.storage.agent.postgres import PgAgentStorage
from phi.vectordb.pgvector import PgVector, SearchType
from phi.tools.duckduckgo import DuckDuckGo
from phi.tools.newspaper4k import Newspaper4k
from pydantic import BaseModel
from phi.knowledge.combined import CombinedKnowledgeBase
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get API key
CONGRESS_API_KEY = os.getenv("CONGRESS_API_KEY")

# Database configuration
db_url = "postgresql+psycopg://ai:ai@localhost:5532/ai"

# Knowledge bases
congress_docs = WebsiteKnowledgeBase(
    urls=[
        f"https://api.congress.gov/v3/bill?api_key={CONGRESS_API_KEY}&limit=50&offset=0",
        f"https://api.congress.gov/v3/bill/117?api_key={CONGRESS_API_KEY}&limit=50",  # Current congress
        f"https://api.congress.gov/v3/summaries?api_key={CONGRESS_API_KEY}&limit=20"  # Bill summaries
    ],
    vector_db=PgVector(
        table_name="congress_docs",
        db_url=db_url,
        search_type=SearchType.hybrid
    ),
)

news_knowledge = WebsiteKnowledgeBase(
    urls=[
        f"https://api.congress.gov/v3/congressional-record?api_key={CONGRESS_API_KEY}&limit=20",  # Recent congressional records
        f"https://api.congress.gov/v3/committee-report?api_key={CONGRESS_API_KEY}&limit=20"  # Recent committee reports
    ],
    max_links=10,
    vector_db=PgVector(
        table_name="congress_news",
        db_url=db_url,
        search_type=SearchType.hybrid
    ),
)

# Combined knowledge base
knowledge_base = CombinedKnowledgeBase(
    sources=[congress_docs, news_knowledge],
    vector_db=PgVector(
        table_name="congress_knowledge",
        db_url=db_url
    )
)

# Storage for persistent memory
storage = PgAgentStorage(
    table_name="congress_agent_sessions",
    db_url=db_url
)

# Create the Congress Analysis Agent
congress_agent = Agent(
    name="Congress Analyst",
    description="I analyze congressional bills and activities to make them easily understandable.",
    knowledge=knowledge_base,
    storage=storage,
    tools=[DuckDuckGo(), Newspaper4k()],
    instructions=[
        "You are an expert at analyzing US Congressional activities and bills.",
        "For each bill, provide a clear summary in plain language that anyone can understand.",
        "Include key points, potential impact, and current status.",
        "When relevant, provide context from historical bills and voting patterns.",
        "Always cite sources and maintain factual accuracy.",
    ],
    show_tool_calls=True,
    read_chat_history=True,
    add_datetime_to_instructions=True,
)

def analyze_recent_bills():
    """Analyze recent congressional bills"""
    # Load knowledge bases if needed
    knowledge_base.load(recreate=False)
    
    # Get analysis from agent
    response = congress_agent.run(
        "Analyze the most recent significant bills introduced in Congress. "
        "Focus on their potential impact on citizens and current status."
    )
    return response

if __name__ == "__main__":
    analysis = analyze_recent_bills()
    print(analysis.content) 