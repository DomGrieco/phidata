from typing import List
from phi.agent import Agent
from phi.model.openai import OpenAIChat
from agents.security_agent import SecurityReviewAgent
from agents.performance_agent import PerformanceReviewAgent
from agents.style_agent import StyleReviewAgent

class CodeReviewTeam(Agent):
    """A team of specialized code review agents."""
    
    def __init__(self):
        # Initialize specialized agents first
        self._security_agent = SecurityReviewAgent()
        self._performance_agent = PerformanceReviewAgent()
        self._style_agent = StyleReviewAgent()
        
        # Initialize the base agent
        super().__init__(
            name="Code Review Team",
            description=(
                "We are a team of expert code reviewers specializing in security, "
                "performance, and code style. We work together to ensure code quality."
            ),
            model=OpenAIChat(model="gpt-4"),
            system_prompt=(
                "You are a team of expert code reviewers. Work together to provide comprehensive "
                "code reviews, ensuring that each specialist focuses on their area of expertise."
            )
        )
    
    async def review_code(self, code_content: str, file_path: str) -> str:
        """Coordinate code review across all agents."""
        
        # Get reviews from each agent
        security_review = await self._security_agent.review_code(code_content, file_path)
        performance_review = await self._performance_agent.review_code(code_content, file_path)
        style_review = await self._style_agent.review_code(code_content, file_path)
        
        # Combine and summarize the reviews
        summary = await self.run(
            f"""Please analyze and summarize the following code reviews:
            
            Security Review:
            {security_review}
            
            Performance Review:
            {performance_review}
            
            Style Review:
            {style_review}
            
            Provide a comprehensive summary that:
            1. Highlights the most critical issues
            2. Groups related issues across different aspects
            3. Suggests a prioritized order for addressing the issues
            4. Identifies any conflicts between different recommendations
            """
        )
        
        return summary 