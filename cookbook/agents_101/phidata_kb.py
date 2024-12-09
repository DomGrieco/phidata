from pathlib import Path

from phi.agent import Agent
from phi.knowledge.json import JSONKnowledgeBase
from phi.vectordb.pgvector import PgVector

db_url = "postgresql+psycopg://ai:ai@localhost:5532/ai"

# Initialize the JSONKnowledgeBase
phidata_knowledge_base = JSONKnowledgeBase(
    path=Path("data/json/phidata"),  
    # Table name: ai.json_phidata_docs
    vector_db=PgVector(
        table_name="json_phidata_docs",
        db_url=db_url,
    ),
    num_documents=5,  # Number of documents to return on search
)
# Load the knowledge base
phidata_knowledge_base.load(recreate=False)

# Initialize the Agent with the knowledge_base
#agent = Agent(
#    knowledge=phidata_knowledge_base,
#    search_knowledge=True,
#)

# Use the agent
#agent.print_response("Ask me about something from the knowledge base", markdown=True)
