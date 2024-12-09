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
from hashlib import sha256
import psycopg2

# Load environment variables
load_dotenv()

# Get API key
CONGRESS_API_KEY = os.getenv("CONGRESS_API_KEY")

# Database configuration
db_url = "postgresql+psycopg://ai:ai@localhost:5532/ai"

# Create data directory if it doesn't exist
data_dir = Path("democracy/data")
data_dir.mkdir(exist_ok=True, parents=True)

def fetch_and_save_congress_data(force_update=False):
    """Fetch data from Congress.gov API and save locally"""
    
    # Create subdirectories for each data type
    for dir_name in ["bills", "records", "reports", "members", "committees", 
                    "meetings", "hearings", "nominations"]:
        data_dir_path = data_dir / dir_name
        data_dir_path.mkdir(exist_ok=True, parents=True)

    urls = {
        "bills": f"https://api.congress.gov/v3/bill?api_key={CONGRESS_API_KEY}&limit=10&format=json",
        "records": f"https://api.congress.gov/v3/congressional-record?api_key={CONGRESS_API_KEY}&limit=5&format=json",
        "reports": f"https://api.congress.gov/v3/committee-report?api_key={CONGRESS_API_KEY}&limit=5&format=json",
        "members": f"https://api.congress.gov/v3/member?api_key={CONGRESS_API_KEY}&limit=5&format=json",
        "committees": f"https://api.congress.gov/v3/committee?api_key={CONGRESS_API_KEY}&limit=5&format=json",
        "meetings": f"https://api.congress.gov/v3/committee-meeting?api_key={CONGRESS_API_KEY}&limit=5&format=json",
        "hearings": f"https://api.congress.gov/v3/hearing?api_key={CONGRESS_API_KEY}&limit=5&format=json",
        "nominations": f"https://api.congress.gov/v3/nomination?api_key={CONGRESS_API_KEY}&limit=5&format=json",
    }

    for name, url in urls.items():
        print(f"\nFetching {name} data...")
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            
            # Save individual items
            items = data.get(name, [])  # Get list of items based on endpoint name
            for item in items:
                # Create unique ID based on available fields
                item_id = item.get('number', '') or item.get('id', '') or item.get('citation', '')
                if item_id:
                    file_path = data_dir / name / f"{item_id}.json"
                    with open(file_path, "w") as f:
                        json.dump(item, f, indent=2)
                    print(f"✓ Saved {name} item: {item_id}")
        else:
            print(f"✗ Error fetching {name}: {response.status_code}")

# Update knowledge bases to use directories
congress_docs = JSONKnowledgeBase(
    path=str(data_dir / "bills"),  # Point to bills directory
    vector_db=PgVector(
        table_name="congress_docs",
        db_url=db_url,
        search_type=SearchType.hybrid
    ),
    text_splitter=1000,
    # Use bill number as document ID
    pre_process_fn=lambda x: {
        'content': x,
        'document_id': x.get('number') if isinstance(x, dict) else None
    }
)

records_knowledge = JSONKnowledgeBase(
    path=str(data_dir / "records"),  # Point to records directory
    vector_db=PgVector(
        table_name="congress_records",
        db_url=db_url,
        search_type=SearchType.hybrid
    ),
    text_splitter=1000
)

reports_knowledge = JSONKnowledgeBase(
    path=str(data_dir / "reports.json"),
    vector_db=PgVector(
        table_name="congress_reports",
        db_url=db_url,
        search_type=SearchType.hybrid
    ),
    text_splitter=2000
)

members_knowledge = JSONKnowledgeBase(
    path=str(data_dir / "members.json"),
    vector_db=PgVector(
        table_name="congress_members",
        db_url=db_url,
        search_type=SearchType.hybrid
    ),
    text_splitter=2000
)

committees_knowledge = JSONKnowledgeBase(
    path=str(data_dir / "committees.json"),
    vector_db=PgVector(
        table_name="congress_committees",
        db_url=db_url,
        search_type=SearchType.hybrid
    ),
    text_splitter=2000
)

meetings_knowledge = JSONKnowledgeBase(
    path=str(data_dir / "committee_meetings.json"),
    vector_db=PgVector(
        table_name="committee_meetings",
        db_url=db_url,
        search_type=SearchType.hybrid
    ),
    text_splitter=2000
)

hearings_knowledge = JSONKnowledgeBase(
    path=str(data_dir / "hearings.json"),
    vector_db=PgVector(
        table_name="congress_hearings",
        db_url=db_url,
        search_type=SearchType.hybrid
    ),
    text_splitter=2000
)

nominations_knowledge = JSONKnowledgeBase(
    path=str(data_dir / "nominations.json"),
    vector_db=PgVector(
        table_name="congress_nominations",
        db_url=db_url,
        search_type=SearchType.hybrid
    ),
    text_splitter=2000
)

# Update combined knowledge base
knowledge_base = CombinedKnowledgeBase(
    sources=[
        congress_docs,
        records_knowledge, 
        reports_knowledge,
        members_knowledge,
        committees_knowledge,
        meetings_knowledge,
        hearings_knowledge,
        nominations_knowledge
    ],
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
    reader=ConstitutionalReader(),
    vector_db=PgVector(
        table_name="constitutional_docs",
        db_url=db_url,
        search_type=SearchType.hybrid
    ),
    text_splitter=2000
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
        "Use ONLY the data from our Combined knowledge base for current information",
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
TEST_KNOWLEDGE_ONLY = True  # Set to False to run full agent analysis

def get_content_hash(content: str) -> str:
    """Generate hash for content to check duplicates"""
    return sha256(content.encode()).hexdigest()

class ContentValidator:
    def __init__(self, db_url: str):
        self.db_url = db_url
        self.conn = psycopg2.connect(db_url)
        
    def is_duplicate(self, table_name: str, content_hash: str) -> bool:
        """Check if content already exists in table"""
        with self.conn.cursor() as cur:
            cur.execute(f"""
                SELECT EXISTS (
                    SELECT 1 FROM ai.{table_name} 
                    WHERE content_hash = %s
                )
            """, (content_hash,))
            return cur.fetchone()[0]

    def add_content_hash(self, table_name: str, content_hash: str):
        """Add content hash to tracking"""
        with self.conn.cursor() as cur:
            cur.execute(f"""
                UPDATE ai.{table_name} 
                SET content_hash = %s 
                WHERE id = (
                    SELECT id FROM ai.{table_name} 
                    WHERE content_hash IS NULL 
                    LIMIT 1
                )
            """, (content_hash,))
        self.conn.commit()

def load_knowledge_bases(force_reload=False):
    """Load all knowledge bases"""
    print("\nLoading Knowledge Bases...")
    print("-------------------------")
    
    try:
        # Load individual knowledge bases
        for kb in [congress_docs, records_knowledge, reports_knowledge, 
                  members_knowledge, committees_knowledge, meetings_knowledge, 
                  hearings_knowledge, nominations_knowledge]:
            # Use upsert to update existing documents and add new ones
            kb.load(recreate=force_reload, upsert=True)
            print(f"✓ Updated {kb.vector_db.table_name}")
            
        # Load combined knowledge base
        knowledge_base.load(recreate=force_reload, upsert=True)
        print("✓ Updated combined knowledge")
        
        # Load constitutional knowledge
        constitutional_knowledge.load(recreate=force_reload, upsert=True)
        print("✓ Updated constitutional knowledge")
        
    except Exception as e:
        print(f"Error loading knowledge bases: {str(e)}")

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

def verify_all_json_data():
    """Verify all JSON files exist and contain data"""
    expected_files = [
        "bills.json",
        "records.json",
        "reports.json",
        "members.json",
        "committees.json",
        "committee_meetings.json",
        "hearings.json",
        "committee_prints.json",
        "nominations.json",
        "treaties.json"
    ]
    
    print("\nVerifying all JSON files:")
    print("------------------------")
    
    for file in expected_files:
        path = data_dir / file
        if path.exists():
            with open(path) as f:
                data = json.load(f)
                print(f"✓ {file:<20} - Keys: {list(data.keys())}")
        else:
            print(f"✗ {file:<20} - File not found")

if __name__ == "__main__":
    # Check for updates
    fetch_and_save_congress_data(force_update=False)
    
    # Verify all JSON data
    verify_all_json_data()
    
    # Load knowledge bases
    load_knowledge_bases(force_reload=False)
    
    # Only run agent analysis if not in test mode
    if not TEST_KNOWLEDGE_ONLY:
        analysis = analyze_bills_with_historical_perspective()
        print(analysis.content)
    else:
        print("\nKnowledge test complete. Agent analysis skipped.") 