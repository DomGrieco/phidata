from historical_agent import (
    congress_analyst, 
    founding_father_analyst, 
    congress_analysis_team,
    load_knowledge_bases
)
from pathlib import Path

def interactive_analysis():
    """Interactive CLI for natural language congressional analysis"""
    print("\nWelcome to the Congressional Analysis System")
    print("------------------------------------------")
    print("Ask any question about Congress, bills, or constitutional implications.")
    print("Examples:")
    print("- What are the recent gun control bills and their constitutional implications?")
    print("- Analyze healthcare legislation from 2023")
    print("- What would the founding fathers think about H.R. 1234?")
    print("- Compare recent privacy laws with constitutional principles")
    
    # Ensure knowledge bases are loaded
    load_knowledge_bases(force_reload=False)
    
    # Create analyses directory if it doesn't exist
    analyses_dir = Path("democracy/analyses")
    analyses_dir.mkdir(exist_ok=True, parents=True)
    
    while True:
        # Get natural language query from user
        query = input("\nWhat would you like to know? (or 'exit' to quit): ")
        
        if query.lower() == 'exit':
            print("\nThank you for using the Congressional Analysis System.")
            break
            
        try:
            # Let the LLM handle query interpretation and analysis
            analysis = congress_analysis_team.run(f"""
                Analyze the following query about congressional legislation 
                and provide both modern and historical constitutional perspectives:
                
                {query}
                
                Consider:
                - Relevant bills and their status
                - Constitutional implications
                - Historical context
                - Current impact
            """)
            
            print("\nAnalysis Results:")
            print("----------------")
            print(analysis.content)
            
            # Option to save
            save = input("\nWould you like to save this analysis? (y/n): ")
            if save.lower() == 'y':
                filename = input("Enter filename to save as: ")
                with open(analyses_dir / f"{filename}.txt", "w") as f:
                    f.write(f"Query: {query}\n\nAnalysis:\n{analysis.content}")
                print(f"Analysis saved to analyses/{filename}.txt")
                
        except Exception as e:
            print(f"\nError processing query: {str(e)}")
            print("Please try rephrasing your question.")

if __name__ == "__main__":
    interactive_analysis() 