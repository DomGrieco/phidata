from historical_agent import (
    congress_analyst, 
    founding_father_analyst, 
    congress_analysis_team,
    load_knowledge_bases
)
from phi.assistant import Assistant
from phi.utils.pprint import pprint_run_response
from pathlib import Path

# Create query interpreter assistant
query_interpreter = Assistant(
    name="Query Interpreter",
    instructions=[
        "You analyze user queries about congressional legislation and format them for detailed analysis.",
        "Identify the main intent and structure the query appropriately.",
        "Format queries to be specific and detailed for the analysis team."
    ],
    debug_mode=True
)

def preprocess_query(query: str) -> str:
    """Use LLM to interpret and format the query appropriately"""
    try:
        response = query_interpreter.run(f"""
        Analyze this user query about congressional legislation: "{query}"
        
        Important: Use ONLY the data from our Congress.gov knowledge base, which contains current 2024 data.
        Do not rely on training data or historical knowledge.
        
        1. Identify the main intent (e.g., recent laws, specific bill analysis, topic analysis)
        2. Format an appropriate query for the analysis team
        
        For example:
        If asking about recent laws, format like this:
        ```
        Using our Congress.gov knowledge base:
        1. Find the most recently enacted bills from our current data
        2. For each enacted bill:
           - List the bill number and exact title
           - Show the exact date enacted
           - Include the latest action status
           - Summarize key provisions
           - Explain current impact
        Sort by most recent enactment date.
        ```
        
        Return only the formatted query as a clear, specific request.
        """, stream=False)
        
        return str(response)
    except Exception as e:
        print(f"Error preprocessing query: {str(e)}")
        return query

def interactive_analysis():
    """Interactive CLI for natural language congressional analysis"""
    print("\nWelcome to the Congressional Analysis System")
    print("------------------------------------------")
    print("Ask any question about Congress, bills, or constitutional implications.")
    print("Examples:")
    print("- What bills recently became law?")
    print("- Tell me about recent gun control legislation")
    print("- What would the founding fathers think about H.R. 1234?")
    
    # Ensure knowledge bases are loaded
    load_knowledge_bases(force_reload=False)
    
    # Create analyses directory if it doesn't exist
    analyses_dir = Path("democracy/analyses")
    analyses_dir.mkdir(exist_ok=True, parents=True)
    
    while True:
        query = input("\nWhat would you like to know? (or 'exit' to quit): ")
        
        if query.lower() == 'exit':
            break
            
        try:
            # Preprocess query using LLM
            formatted_query = preprocess_query(query)
            print("\nInterpreted Query:", formatted_query)
            
            # Run analysis with formatted query and handle streaming
            print("\nAnalysis Results:")
            print("----------------")
            analysis_content = ""
            for chunk in congress_analysis_team.run(formatted_query, stream=True):
                if hasattr(chunk, 'content') and chunk.content:
                    analysis_content += chunk.content
                    print(chunk.content, end="", flush=True)
            
            # Option to save
            if analysis_content:
                save = input("\n\nWould you like to save this analysis? (y/n): ")
                if save.lower() == 'y':
                    filename = input("Enter filename to save as: ")
                    with open(analyses_dir / f"{filename}.txt", "w") as f:
                        f.write(f"Original Query: {query}\nInterpreted Query: {formatted_query}\n\nAnalysis:\n{analysis_content}")
                    print(f"Analysis saved to analyses/{filename}.txt")
                
        except Exception as e:
            print(f"\nError processing query: {str(e)}")
            print("Please try rephrasing your question.")

if __name__ == "__main__":
    interactive_analysis() 