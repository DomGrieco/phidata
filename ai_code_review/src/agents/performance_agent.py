from phi.agent import Agent
from phi.model.openai import OpenAIChat

class PerformanceReviewAgent(Agent):
    """Agent specialized in performance code reviews using Phidata framework."""
    
    def __init__(self):
        super().__init__(
            name="Performance Review Agent",
            description=(
                "I am a performance optimization expert that reviews code for efficiency issues. "
                "I identify performance bottlenecks, memory leaks, and optimization opportunities."
            ),
            model=OpenAIChat(model="gpt-4"),
            system_prompt=(
                "You are an expert performance code reviewer. Your task is to:"
                "\n1. Identify performance bottlenecks and inefficiencies"
                "\n2. Detect potential memory leaks and resource management issues"
                "\n3. Suggest algorithmic improvements and optimizations"
                "\n4. Provide benchmarking suggestions when relevant"
                "\n5. Consider both time and space complexity"
            )
        )
    
    async def review_code(self, code_content: str, file_path: str) -> str:
        """Review code for performance issues."""
        
        response = await self.run(
            f"""Please review this code for performance issues:
            
            File: {file_path}
            ```python
            {code_content}
            ```
            
            Focus on:
            1. Time complexity analysis
            2. Memory usage and potential leaks
            3. Resource management
            4. Algorithmic efficiency
            5. Caching opportunities
            6. Database query optimization (if applicable)
            
            Format each issue as:
            - Impact: (high/medium/low)
            - Line number: (if applicable)
            - Issue: (description)
            - Optimization: (suggestion)
            - Expected improvement: (estimated performance gain)
            """
        )
        return response 