from phi.agent import Agent
from phi.knowledge.website import WebsiteKnowledgeBase
from phi.vectordb.pgvector import PgVector, SearchType
from knowledge_bases import (
    constitutional_summaries,
    federalism_knowledge,
    bill_of_rights_knowledge
)

# Database configuration
db_url = "postgresql+psycopg://ai:ai@localhost:5532/ai"

# Create knowledge bases
constitutional_summaries = WebsiteKnowledgeBase(
    urls=["https://www.archives.gov/founding-docs/constitution-transcript"],
    vector_db=PgVector(
        table_name="constitutional_summaries",
        db_url=db_url,
        search_type=SearchType.hybrid
    ),
    text_splitter=2000,
    max_links=0,
    selectors=["#main-col"],
    exclude_selectors=[
        "header",
        "footer",
        "nav",
        ".usa-banner",
        ".usa-nav"
    ]
)

federalism_knowledge = WebsiteKnowledgeBase(
    urls=["https://guides.loc.gov/federalist-papers/full-text"],
    vector_db=PgVector(
        table_name="federalism_knowledge",
        db_url=db_url,
        search_type=SearchType.hybrid
    ),
    text_splitter=2000,
    max_links=100,
    selectors=[".col-md-9"],
    link_selectors=[".col-md-9 a"],
    exclude_selectors=[
        "header",
        "footer",
        "nav",
        ".usa-banner",
        ".usa-nav",
        ".breadcrumb",
        ".pagination"
    ],
    exclude_links=[
        lambda url: not url.startswith("https://guides.loc.gov/federalist-papers"),
        lambda url: "print" in url,
        lambda url: "pdf" in url
    ]
)

bill_of_rights_knowledge = WebsiteKnowledgeBase(
    urls=["https://www.archives.gov/founding-docs/bill-of-rights-transcript"],
    vector_db=PgVector(
        table_name="bill_of_rights_knowledge",
        db_url=db_url,
        search_type=SearchType.hybrid
    ),
    text_splitter=2000,
    max_links=0,
    selectors=["#main-col"],
    exclude_selectors=[
        "header",
        "footer",
        "nav",
        ".usa-banner",
        ".usa-nav"
    ]
)

# Load knowledge bases
def init_knowledge_bases(force_reload=False):
    """Initialize all knowledge bases"""
    print("\nInitializing knowledge bases...")
    constitutional_summaries.load(recreate=force_reload, upsert=True)
    federalism_knowledge.load(recreate=force_reload, upsert=True)
    bill_of_rights_knowledge.load(recreate=force_reload, upsert=True)

# Specialized Expert Agents
federalism_expert = Agent(
    name="Federalism Expert",
    role="Analyzes legislation through federalism principles",
    knowledge=federalism_knowledge,
    instructions=[
        "Focus only on federal vs state power implications",
        "Reference key federalism principles from founding documents",
        "Analyze power distribution between federal and state governments",
        "Consider state sovereignty and federal limits",
    ]
)

civil_rights_expert = Agent(
    name="Civil Rights Expert",
    role="Analyzes legislation through Bill of Rights lens",
    knowledge=bill_of_rights_knowledge,
    instructions=[
        "Focus on individual rights and liberties",
        "Reference specific amendments and rights",
        "Consider impact on constitutional protections",
        "Analyze potential civil rights implications",
    ]
)

constitutional_expert = Agent(
    name="Constitutional Structure Expert",
    role="Analyzes legislation through constitutional framework",
    knowledge=constitutional_summaries,
    instructions=[
        "Focus on constitutional structure and principles",
        "Consider separation of powers",
        "Analyze checks and balances implications",
        "Reference specific constitutional provisions",
    ]
) 