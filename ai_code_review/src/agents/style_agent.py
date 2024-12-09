from phi.agent import Agent
from phi.model.openai import OpenAIChat

class StyleReviewAgent(Agent):
    """Agent specialized in code style reviews using Phidata framework."""
    
    def __init__(self):
        super().__init__(
            name="Style Review Agent",
            description=(
                "I am a code style expert that reviews code for readability and maintainability. "
                "I ensure code follows PEP 8 guidelines and best practices for Python."
            ),
            model=OpenAIChat(model="gpt-4"),
            system_prompt=(
                "You are an expert code style reviewer. Your task is to:"
                "\n1. Ensure compliance with PEP 8 guidelines"
                "\n2. Check code readability and clarity"
                "\n3. Verify proper documentation and comments"
                "\n4. Assess naming conventions and consistency"
                "\n5. Review code organization and structure"
            )
        )
    
    async def review_code(self, code_content: str, file_path: str) -> str:
        """Review code for style issues."""
        
        response = await self.run(
            f"""Please review this code for style and readability:
            
            File: {file_path}
            ```python
            {code_content}
            ```
            
            Focus on:
            1. PEP 8 compliance
            2. Variable and function naming
            3. Code documentation and comments
            4. Code organization and structure
            5. Consistency in style
            6. Readability and maintainability
            
            Format each issue as:
            - Type: (style/documentation/organization)
            - Line number: (if applicable)
            - Issue: (description)
            - Suggestion: (how to improve)
            """
        )
        return response 