from phi.knowledge.website import WebsiteKnowledgeBase
from phi.knowledge.json import JSONKnowledgeBase
from phi.vectordb.pgvector import PgVector, SearchType
from phi.document.base import Document

# Database configuration
db_url = "postgresql+psycopg://ai:ai@localhost:5532/ai"

def summarize_constitutional_text(text: str) -> str:
    """Create focused summaries of constitutional texts"""
    # This would be implemented with a summarization model
    return text  # Placeholder for now

# Specialized Constitutional Knowledge
constitutional_summaries = WebsiteKnowledgeBase(
    urls=["https://www.archives.gov/founding-docs/constitution-transcript"],
    vector_db=PgVector(
        table_name="constitutional_summaries",
        db_url=db_url,
        search_type=SearchType.hybrid
    ),
    pre_process_fn=lambda x: {
        'content': summarize_constitutional_text(x),
        'document_id': 'constitution_summary'
    }
)

federalism_knowledge = WebsiteKnowledgeBase(
    urls=["https://guides.loc.gov/federalist-papers/full-text"],
    vector_db=PgVector(
        table_name="federalism_knowledge",
        db_url=db_url,
        search_type=SearchType.hybrid
    ),
    pre_process_fn=lambda x: {
        'content': summarize_constitutional_text(x),
        'document_id': 'federalism_principles'
    }
)

bill_of_rights_knowledge = WebsiteKnowledgeBase(
    urls=["https://www.archives.gov/founding-docs/bill-of-rights-transcript"],
    vector_db=PgVector(
        table_name="bill_of_rights_knowledge",
        db_url=db_url,
        search_type=SearchType.hybrid
    ),
    pre_process_fn=lambda x: {
        'content': summarize_constitutional_text(x),
        'document_id': 'rights_principles'
    }
) 