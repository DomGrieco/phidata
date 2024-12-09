from phi.agent import Agent
from phi.model.openai import OpenAIChat

class SecurityReviewAgent(Agent):
    """Agent specialized in security code reviews using Phidata framework."""
    
    def __init__(self):
        super().__init__(
            name="Security Review Agent",
            description=(
                "I am a security expert that reviews code for potential security vulnerabilities. "
                "I check for issues like hardcoded credentials, injection vulnerabilities, and unsafe operations."
            ),
            model=OpenAIChat(model="gpt-4"),
            system_prompt=(
                "You are an expert security code reviewer. Your task is to:"
                "\n1. Identify security vulnerabilities in code"
                "\n2. Assess the severity of each issue"
                "\n3. Provide clear explanations of the risks"
                "\n4. Suggest secure alternatives and fixes"
            )
        )
    
    async def review_code(self, code_content: str, file_path: str) -> str:
        """Review code for security vulnerabilities."""
        
        response = await self.run(
            f"""Please review this code for security vulnerabilities:
            
            File: {file_path}
            ```python
            {code_content}
            ```
            
            Focus on:
            1. Authentication/Authorization issues
            2. Data validation and sanitization
            3. Cryptographic misuse
            4. Information disclosure
            5. Access control
            
            Format each issue as:
            - Severity: (critical/major/minor)
            - Line number: (if applicable)
            - Issue: (description)
            - Fix: (suggestion)
            """
        )
        return response
    
    async def validate_fix(self, original_code: str, modified_code: str) -> str:
        """Validate that security fixes don't introduce new vulnerabilities."""
        
        response = await self.run(
            f"""Please compare the original and modified code for security implications:
            
            Original:
            ```python
            {original_code}
            ```
            
            Modified:
            ```python
            {modified_code}
            ```
            
            1. Are all original security issues fixed?
            2. Have any new security issues been introduced?
            3. Are the fixes implemented securely?
            
            Provide a detailed analysis focusing only on security aspects.
            """
        )
        return response 