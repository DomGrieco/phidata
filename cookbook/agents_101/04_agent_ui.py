from phi.agent import Agent
from phi.model.openai import OpenAIChat
from phi.tools.duckduckgo import DuckDuckGo
from phi.tools.yfinance import YFinanceTools
from phi.storage.agent.sqlite import SqlAgentStorage
from phi.playground import Playground, serve_playground_app
#from phidata_kb import phidata_knowledge_base
from phi.knowledge.json import JSONKnowledgeBase
from phi.vectordb.pgvector import PgVector
from pathlib import Path

# Get the current file's directory
current_dir = Path(__file__).parent.resolve()
# Go up one level to the cookbook directory if needed
cookbook_dir = current_dir.parent

print(f"Looking for JSON files in: {current_dir / 'data' / 'json' / 'phidata'}")

web_agent = Agent(
    name="Web Agent",
    agent_id="web_agent",
    role="Search the web for information",
    model=OpenAIChat(id="gpt-4o"),
    tools=[DuckDuckGo()],
    instructions=["Always include sources"],
    storage=SqlAgentStorage(table_name="web_agent_sessions", db_file="tmp/agents.db"),
    markdown=True,
)

finance_agent = Agent(
    name="Finance Agent",
    agent_id="finance_agent",
    role="Get financial data",
    model=OpenAIChat(id="gpt-4o"),
    tools=[YFinanceTools(stock_price=True, analyst_recommendations=True, company_info=True, company_news=True)],
    instructions=["Always use tables to display data"],
    storage=SqlAgentStorage(table_name="finance_agent_sessions", db_file="tmp/agents.db"),
    markdown=True,
)

db_url = "postgresql+psycopg://ai:ai@localhost:5532/ai"

# Initialize the JSONKnowledgeBase
phidata_knowledge_base = JSONKnowledgeBase(
    #path=Path("data/json/phidata"),  
    path=current_dir / "data" / "json" / "phidata",
    # Table name: ai.json_phidata_docs
    vector_db=PgVector(
        table_name="json_phidata_docs",
        db_url=db_url,
    ),
    batch_size=20,
    num_documents=5,  # Number of documents to return on search
)
# Load the knowledge base
phidata_knowledge_base.load(recreate=False)

phidatahelper_agent = Agent(
    name="Phidata Helper",
    agent_id="phidatahelper_agent",
    role="Help with Phidata information.",
    model=OpenAIChat(id="gpt-4o"),
    tools=[DuckDuckGo()],
    knowledge=phidata_knowledge_base,
    search_knowledge=True,
    instructions=["Always include sources"],
    storage=SqlAgentStorage(table_name="phidatahelper_agent_sessions", db_file="tmp/agents.db"),
    markdown=True,
    debug_mode=True,
)

agent_team = Agent(
    name="Agent Team",
    agent_id="agent_team",
    team=[web_agent, finance_agent, phidatahelper_agent],
    storage=SqlAgentStorage(table_name="agent_team_sessions", db_file="tmp/agents.db"),
    markdown=True,
)

app = Playground(agents=[finance_agent, web_agent, phidatahelper_agent, agent_team]).get_app()

if __name__ == "__main__":
    serve_playground_app("04_agent_ui:app", reload=True)
