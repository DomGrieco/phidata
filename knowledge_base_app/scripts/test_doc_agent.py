import asyncio
import logging
from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown
from rich.traceback import install

from app.agents.documentation_agent import DocumentationAgent

# Install rich traceback handler
install(show_locals=True)

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

console = Console()

async def main():
    try:
        # Initialize the Documentation Agent
        logger.info("Initializing DocumentationAgent...")
        doc_agent = DocumentationAgent()
        
        # Print current stats
        logger.info("Getting knowledge base statistics...")
        stats = doc_agent.get_stats()
        if stats["status"] == "success":
            console.print(Panel(
                "\n".join([
                    f"Total Documents: {stats['stats']['total_documents']}",
                    f"PDF Documents: {stats['stats']['pdf_documents']}",
                    f"Text Documents: {stats['stats']['text_documents']}"
                ]),
                title="Knowledge Base Statistics"
            ))
        else:
            console.print(Panel(
                f"[red]Error getting statistics: {stats['message']}[/red]",
                title="Error"
            ))
        
        while True:
            # Get user input
            question = input("\nEnter your question (or 'exit' to quit): ")
            
            if question.lower() == 'exit':
                break
            
            # Process the query
            logger.info(f"Processing query: {question}")
            response = await doc_agent.query(question)
            
            if response["status"] == "success":
                # Print the response
                console.print(Panel(
                    Markdown(response["response"]),
                    title="Agent Response"
                ))
                
                # Print relevant documents if any
                if response["relevant_documents"]:
                    console.print(Panel(
                        "\n".join([f"- {doc}" for doc in response["relevant_documents"]]),
                        title="Relevant Documents"
                    ))
            else:
                console.print(Panel(
                    f"[red]Error: {response['message']}\nDetails: {response.get('error', 'No additional details')}[/red]",
                    title="Error"
                ))
    except Exception as e:
        logger.error("Error in main loop", exc_info=True)
        console.print(Panel(
            f"[red]Critical Error: {str(e)}[/red]",
            title="Critical Error"
        ))

if __name__ == "__main__":
    asyncio.run(main()) 