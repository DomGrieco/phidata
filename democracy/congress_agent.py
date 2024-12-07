from typing import Optional, List
from datetime import datetime
from phi.agent import Agent
from phi.knowledge.pdf import PDFUrlKnowledgeBase, PDFKnowledgeBase
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

# Create Constitutional Knowledge Base
constitutional_knowledge = PDFKnowledgeBase(
    urls=[
        "https://www.archives.gov/founding-docs/constitution-transcript",
        "https://guides.loc.gov/federalist-papers/full-text",
        "https://www.archives.gov/founding-docs/bill-of-rights-transcript"
    ],
    vector_db=PgVector(
        table_name="constitutional_docs",
        db_url=db_url,
        search_type=SearchType.hybrid
    ),
)

# Modern Congress Analyst
congress_analyst = Agent(
    name="Modern Congress Analyst",
    role="Analyzes current congressional activities and provides objective summaries",
    knowledge=knowledge_base,
    tools=[DuckDuckGo(), Newspaper4k()],
    instructions=[
        "Analyze current congressional bills and activities objectively",
        "Focus on summarizing key points, impact, and status",
        "Provide clear explanations without historical interpretation",
    ],
)

# Constitutional Perspective Analyst
founding_father_analyst = Agent(
    name="Constitutional Perspective Analyst",
    role="Provides historical constitutional perspective on modern legislation",
    knowledge=constitutional_knowledge,
    instructions=[
        "You are an expert on the US Constitution, Federalist Papers, and founding principles",
        "Analyze modern legislation through the lens of the founding fathers",
        "Consider constitutional principles, federalism, and original intent",
        "Reference specific writings, debates, or principles from the founding era",
        "Be direct about potential constitutional concerns or alignments",
    ],
)

# Team Leader Agent
congress_analysis_team = Agent(
    name="Congressional Analysis Team",
    team=[congress_analyst, founding_father_analyst],
    storage=storage,
    instructions=[
        "First, have the Modern Congress Analyst summarize the current legislation",
        "Then, ask the Constitutional Perspective Analyst to analyze it from a founding fathers' perspective",
        "Highlight any interesting contrasts between modern and founding era perspectives",
        "Focus on constitutional principles, federalism, and separation of powers",
    ],
    show_tool_calls=True,
    read_chat_history=True,
    add_datetime_to_instructions=True,
)

# Storage for persistent memory
storage = PgAgentStorage(
    table_name="congress_agent_sessions",
    db_url=db_url
)

def analyze_bills_with_historical_perspective():
    """Analyze bills with both modern and historical constitutional perspectives"""
    # Load knowledge bases
    knowledge_base.load(recreate=False)
    constitutional_knowledge.load(recreate=False)
    
    # Get team analysis
    response = congress_analysis_team.run(
        "Analyze the most recent significant bills in Congress, "
        "comparing modern implementation with founding constitutional principles. "
        "What would the founding fathers think about these changes?"
    )
    return response

if __name__ == "__main__":
    analysis = analyze_bills_with_historical_perspective()
    print(analysis.content) 