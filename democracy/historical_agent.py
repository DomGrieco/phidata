from typing import Optional, List
from datetime import datetime
from phi.agent import Agent
from phi.knowledge.pdf import PDFUrlKnowledgeBase, PDFKnowledgeBase
from phi.knowledge.website import WebsiteKnowledgeBase
from phi.knowledge.json import JSONKnowledgeBase
from phi.storage.agent.postgres import PgAgentStorage
from phi.vectordb.pgvector import PgVector, SearchType
from phi.tools.duckduckgo import DuckDuckGo
from phi.tools.newspaper4k import Newspaper4k
from phi.knowledge.combined import CombinedKnowledgeBase
import os
from dotenv import load_dotenv
import json
import requests
from pathlib import Path
from phi.document.reader.website import WebsiteReader
from phi.document.base import Document
from bs4 import BeautifulSoup

# Load environment variables
load_dotenv()

# Get API key
CONGRESS_API_KEY = os.getenv("CONGRESS_API_KEY")

# Database configuration
db_url = "postgresql+psycopg://ai:ai@localhost:5532/ai"

# Create data directory if it doesn't exist
data_dir = Path("democracy/data")
data_dir.mkdir(exist_ok=True, parents=True)

def fetch_and_save_congress_data():
    """Fetch data from Congress.gov API and save locally"""
    urls = {
        "bills": f"https://api.congress.gov/v3/bill?api_key={CONGRESS_API_KEY}&limit=50&offset=0&format=json",
        "summaries": f"https://api.congress.gov/v3/summaries?api_key={CONGRESS_API_KEY}&limit=20&format=json",
        "records": f"https://api.congress.gov/v3/congressional-record?api_key={CONGRESS_API_KEY}&limit=20&format=json",
        "reports": f"https://api.congress.gov/v3/committee-report?api_key={CONGRESS_API_KEY}&limit=20&format=json"
    }
    
    for name, url in urls.items():
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            print(f"\nFetched {name} data:")
            print(f"Response structure: {list(data.keys())}")
            with open(data_dir / f"{name}.json", "w") as f:
                json.dump(data, f, indent=2)

# Update knowledge bases to use simpler configuration
congress_docs = JSONKnowledgeBase(
    path=str(data_dir / "bills.json"),
    vector_db=PgVector(
        table_name="congress_docs",
        db_url=db_url,
        search_type=SearchType.hybrid
    )
)

# Create separate knowledge bases for records and reports
records_knowledge = JSONKnowledgeBase(
    path=str(data_dir / "records.json"),
    vector_db=PgVector(
        table_name="congress_records",
        db_url=db_url,
        search_type=SearchType.hybrid
    )
)

reports_knowledge = JSONKnowledgeBase(
    path=str(data_dir / "reports.json"),
    vector_db=PgVector(
        table_name="congress_reports",
        db_url=db_url,
        search_type=SearchType.hybrid
    )
)

# Combined knowledge base
knowledge_base = CombinedKnowledgeBase(
    sources=[congress_docs, records_knowledge, reports_knowledge],  # Include all sources
    vector_db=PgVector(
        table_name="congress_knowledge",
        db_url=db_url
    )
)

class ConstitutionalReader(WebsiteReader):
    def __init__(self):
        super().__init__()  # Initialize parent class
        self._session = requests.Session()  # Use _session instead of session
    
    @property
    def session(self):
        return self._session

    def read(self, url: str) -> List[Document]:
        print(f"\nProcessing URL: {url}")
        response = self.session.get(url)
        soup = BeautifulSoup(response.content, 'html.parser')
        documents = []

        # Handle archives.gov pages
        if 'archives.gov' in url:
            content_div = soup.find('div', id='main-col')
            print(f"Found archives.gov content div: {bool(content_div)}")
            if content_div:
                # Clean up the content
                [s.extract() for s in content_div.find_all(['script', 'style'])]
                content = content_div.get_text(separator='\n', strip=True)
                print(f"Content length: {len(content)}")
                documents.append(Document(content=content))

        # Handle loc.gov pages
        elif 'loc.gov' in url:
            content_div = soup.find('div', class_='col-md-9')
            print(f"Found loc.gov content div: {bool(content_div)}")
            if content_div:
                # Clean up the content
                [s.extract() for s in content_div.find_all(['script', 'style'])]
                content = content_div.get_text(separator='\n', strip=True)
                print(f"Content length: {len(content)}")
                documents.append(Document(content=content))

        print(f"Documents created: {len(documents)}")
        return documents

# Update constitutional knowledge to use custom reader
constitutional_knowledge = WebsiteKnowledgeBase(
    urls=[
        "https://www.archives.gov/founding-docs/constitution-transcript",
        "https://guides.loc.gov/federalist-papers/full-text", 
        "https://www.archives.gov/founding-docs/bill-of-rights-transcript"
    ],
    max_links=0,
    reader=ConstitutionalReader(),  # Switch back to custom reader
    vector_db=PgVector(
        table_name="constitutional_docs",
        db_url=db_url,
        search_type=SearchType.hybrid
    )
)

# Storage for persistent memory
storage = PgAgentStorage(
    table_name="congress_agent_sessions",
    db_url=db_url
)

# Modern Congress Analyst
congress_analyst = Agent(
    name="Modern Congress Analyst",
    role="Analyzes current congressional activities and provides objective summaries",
    knowledge=knowledge_base,
    tools=[DuckDuckGo(), Newspaper4k()],
    instructions=[
        "Use ONLY the data from our Congress.gov knowledge base for current information",
        "When analyzing recent bills, focus on actual enactment dates and current status",
        "Provide specific bill numbers, dates, and exact titles from our knowledge base",
        "Do not rely on training data for current legislative information",
        "Focus on summarizing key points, impact, and status from our current data",
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
    debug_mode=True
)

# Configuration flags
TEST_KNOWLEDGE_ONLY = False  # Set to False to run full agent analysis

def load_knowledge_bases(force_reload=False):
    """Load all knowledge bases"""
    print("\nLoading Knowledge Bases...")
    print("-------------------------")
    
    if force_reload:
        print("Force reloading all knowledge...")
        # Initialize JSON knowledge bases first
        congress_docs.load(recreate=True, upsert=True)
        records_knowledge.load(recreate=True, upsert=True)
        reports_knowledge.load(recreate=True, upsert=True)
        # Then load combined and constitutional
        knowledge_base.load(recreate=True, upsert=True)
        constitutional_knowledge.load(recreate=True, upsert=True)
    else:
        print("Updating knowledge bases...")
        # Initialize JSON knowledge bases first
        congress_docs.load(recreate=False, upsert=True)
        records_knowledge.load(recreate=False, upsert=True)
        reports_knowledge.load(recreate=False, upsert=True)
        # Then load combined and constitutional
        knowledge_base.load(recreate=False, upsert=True)
        constitutional_knowledge.load(recreate=False, upsert=True)

def analyze_bills_with_historical_perspective():
    """Analyze bills with both modern and historical constitutional perspectives"""
    # Load knowledge bases without recreation
    load_knowledge_bases(force_reload=False)
    
    # Get team analysis
    response = congress_analysis_team.run(
        "Analyze the most recent significant bills in Congress, "
        "comparing modern implementation with founding constitutional principles. "
        "What would the founding fathers think about these changes?"
    )
    return response

def verify_json_data():
    """Verify the content of saved JSON files"""
    for file in ["bills.json", "records.json", "reports.json"]:
        path = data_dir / file
        if path.exists():
            with open(path) as f:
                data = json.load(f)
                print(f"\nVerifying {file}:")
                print(f"Structure: {list(data.keys())}")
                print(f"Size: {len(str(data))} characters")

if __name__ == "__main__":
    # Fetch fresh data if needed
    data_updated = False
    if not (data_dir / "bills.json").exists():
        fetch_and_save_congress_data()
        data_updated = True
    
    # Verify JSON data
    verify_json_data()
    
    # Load knowledge bases
    load_knowledge_bases(force_reload=data_updated)
    
    # Only run agent analysis if not in test mode
    if not TEST_KNOWLEDGE_ONLY:
        analysis = analyze_bills_with_historical_perspective()
        print(analysis.content)
    else:
        print("\nKnowledge test complete. Agent analysis skipped.") 