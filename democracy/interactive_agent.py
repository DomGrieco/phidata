from workflow import CongressAnalysisWorkflow
from phi.memory.db.postgres import PgMemoryDb
from phi.assistant import Assistant
from phi.memory import AgentMemory
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Add database configuration
db_url = "postgresql+psycopg://ai:ai@localhost:5532/ai"

# Create memory database with proper configuration
agent_memory = AgentMemory(
    db=PgMemoryDb(
        table_name="agent_memory",
        db_url=db_url
    ),
    create_user_memories=True,
    create_session_summary=True
)

# Create workflow
analysis_workflow = CongressAnalysisWorkflow()

def interactive_analysis():
    """Interactive CLI with workflow management"""
    print("\nWelcome to the Congressional Analysis System")
    print("------------------------------------------")
    
    while True:
        query = input("\nWhat would you like to know? (or 'exit' to quit): ")
        
        if query.lower() == 'exit':
            break
            
        try:
            logger.info(f"Processing query: {query}")
            
            # Run analysis workflow and consume the generator
            for event in analysis_workflow.run(query):
                if hasattr(event, 'content') and event.content:
                    print("\nAnalysis Result:")
                    print("-----------------")
                    print(event.content)
                    logger.info("Generated content successfully")
                    
                    # Save to memory
                    try:
                        run = {
                            "input": query,
                            "output": event.content
                        }
                        agent_memory.add_run(run)
                        logger.info("Successfully saved to database")
                    except Exception as db_error:
                        logger.error(f"Failed to save to database: {str(db_error)}")
                        
        except Exception as e:
            logger.error(f"Error processing query: {str(e)}")
            print(f"\nError processing query: {str(e)}")

if __name__ == "__main__":
    interactive_analysis() 