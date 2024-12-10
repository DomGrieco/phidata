"""Code review team coordinator."""

from phi.agent import Agent
from phi.model.openai import OpenAIChat
from phi.tools.file import FileTools
from phi.storage.agent.sqlite import SqlAgentStorage

from ai_code_review.config.settings import DB_FILE, DEFAULT_MODEL
from ai_code_review.agents import (
    security_agent, review_security,
    performance_agent, review_performance,
    documentation_agent, review_documentation,
    testing_agent, review_testing
)

# Team leader instructions
TEAM_INSTRUCTIONS = [
    "Coordinate code review activities",
    "Synthesize findings from team members",
    "Prioritize issues and recommendations",
    "Generate clear summary reports",
    "Manage review workflow:",
    "1. Security review first",
    "2. Performance analysis",
    "3. Documentation review",
    "4. Testing review",
    "5. Final synthesis and recommendations"
]

# Create team leader
review_team = Agent(
    name="Code Review Team",
    role="Lead code review coordinator managing the review process",
    team=[security_agent, performance_agent, documentation_agent, testing_agent],
    model=OpenAIChat(model=DEFAULT_MODEL),
    tools=[FileTools()],
    storage=SqlAgentStorage(table_name="review_team", db_file=DB_FILE),
    instructions=TEAM_INSTRUCTIONS,
    add_history_to_messages=True,
    show_tool_calls=True,
    markdown=True
)

async def review_code(code_content: str, file_path: str) -> dict:
    """
    Coordinate the code review process across all agents.
    
    Args:
        code_content: The code to review
        file_path: Path to the file being reviewed
        
    Returns:
        dict: Structured review results from all agents
    """
    # Run specialized reviews
    security_review = await review_security(code_content)
    performance_review = await review_performance(code_content)
    docs_review = await review_documentation(code_content)
    testing_review = await review_testing(code_content)
    
    # Generate final report
    summary = await review_team.run(
        f"""Synthesize the following reviews for {file_path}:
        
        Security Review:
        {security_review}
        
        Performance Review:
        {performance_review}
        
        Documentation Review:
        {docs_review}
        
        Testing Review:
        {testing_review}
        
        Provide a prioritized list of issues and recommendations.
        """
    )
    
    return {
        "file_path": file_path,
        "security": security_review,
        "performance": performance_review,
        "documentation": docs_review,
        "testing": testing_review,
        "summary": summary
    } 