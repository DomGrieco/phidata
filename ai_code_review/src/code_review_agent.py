from phi.agent import Agent
from phi.model.openai import OpenAIChat

class CodeReviewAgent(Agent):
    """An agent that performs comprehensive code reviews."""
    
    def __init__(self):
        super().__init__(
            name="Code Review Agent",
            description=(
                "I am an expert code reviewer that analyzes code for security, "
                "performance, and style issues. I provide comprehensive feedback "
                "to help improve code quality."
            ),
            model=OpenAIChat(model="gpt-4"),
            system_prompt=(
                "You are an expert code reviewer with deep knowledge in:"
                "\n1. Security: Identifying vulnerabilities and security best practices"
                "\n2. Performance: Detecting inefficiencies and optimization opportunities"
                "\n3. Style: Ensuring code follows best practices and is maintainable"
                "\n\nFor each code review, analyze all these aspects and provide clear, "
                "actionable feedback with specific recommendations."
            )
        )
    
    async def review_code(self, code: str) -> str:
        """Review code for security, performance, and style issues."""
        
        response = await self.run(
            f"""Please review this code comprehensively:

            ```python
            {code}
            ```
            
            Analyze the following aspects:
            
            1. Security:
               - Check for vulnerabilities
               - Identify security risks
               - Suggest secure alternatives
            
            2. Performance:
               - Identify inefficiencies
               - Analyze complexity
               - Suggest optimizations
            
            3. Style and Maintainability:
               - Check PEP 8 compliance
               - Review naming and organization
               - Assess documentation
            
            Format your response as:
            1. Critical Issues (if any)
            2. Security Analysis
            3. Performance Analysis
            4. Style Analysis
            5. Prioritized Recommendations
            """
        )
        
        return response 