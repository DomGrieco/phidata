"""Code generation and modification agent."""

from typing import Optional, Dict, Any, List
from phi.agent import Agent, AgentKnowledge
from phi.knowledge.text import TextKnowledgeBase
from phi.tools.python import PythonTools
from phi.storage.agent.sqlite import SqlAgentStorage
from phi.model.openai import OpenAIChat
from rich import print as rprint
from rich.panel import Panel
from rich.markdown import Markdown

from ..config.settings import (
    DEFAULT_MODEL,
    DEFAULT_TEMPERATURE,
    MAX_ITERATIONS,
    QUALITY_THRESHOLDS,
    CODE_PATTERNS_PATH,
    DB_FILE
)

# Agent instructions
CODE_AGENT_INSTRUCTIONS = [
    "You are a Python code implementation expert.",
    "Your role is to implement code based on task requirements.",
    "Follow these guidelines:",
    "1. Write clean, efficient, and well-documented code",
    "2. Follow Python best practices and PEP standards",
    "3. Include proper error handling",
    "4. Add type hints where appropriate",
    "5. Include docstrings and comments",
    "6. Consider security implications",
    "7. Optimize for performance where possible",
    "8. Format your responses in markdown",
    "9. Use code blocks for implementation",
    "10. In each iteration, focus on specific improvements"
]

class CodeAgent:
    def __init__(self):
        """Initialize the Code Agent with Phidata components."""
        # Create knowledge base
        knowledge_base = AgentKnowledge(
            sources=[TextKnowledgeBase(path=CODE_PATTERNS_PATH)],
        )
        
        # Initialize the model
        model = OpenAIChat(
            model=DEFAULT_MODEL,
            temperature=DEFAULT_TEMPERATURE
        )
        
        self.agent = Agent(
            name="Code Implementation Agent",
            role="Expert Python developer implementing code based on requirements",
            instructions=CODE_AGENT_INSTRUCTIONS,
            model=model,
            tools=[PythonTools()],
            knowledge=knowledge_base,
            storage=SqlAgentStorage(
                table_name="code_agent",
                db_file=DB_FILE
            ),
            show_tool_calls=True,
            markdown=True,
            debug_mode=True,
            search_knowledge=True
        )
        
    def implement_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """
        Implement code based on task requirements.
        
        Args:
            task: Task definition including requirements
            
        Returns:
            Dict containing implementation results
        """
        iterations = 0
        current_code = None
        improvement_goals = [
            "Initial implementation meeting basic requirements",
            "Optimize performance and add comprehensive error handling",
            "Enhance documentation and add usage examples",
            "Final polish and edge case handling"
        ]
        
        rprint(Panel.fit("🚀 Starting Code Implementation", title="Task Processing"))
        
        while iterations < min(MAX_ITERATIONS, len(improvement_goals)):
            current_goal = improvement_goals[iterations]
            rprint(f"\n[bold cyan]Iteration {iterations + 1}/{min(MAX_ITERATIONS, len(improvement_goals))}[/bold cyan]")
            rprint(f"[bold yellow]Goal: {current_goal}[/bold yellow]")
            
            # Generate or modify code
            response = self.agent.run(
                f"""Implement or improve code for this task:
                Description: {task['description']}
                Requirements: {task['requirements']}
                Previous Code: {current_code if current_code else 'None'}
                Iteration: {iterations + 1}/{min(MAX_ITERATIONS, len(improvement_goals))}
                Current Goal: {current_goal}
                
                Format your response in markdown with code blocks.
                Include a section explaining how this iteration improves upon the previous one.
                """
            )
            
            # Extract code from response
            current_code = str(response)
            iterations += 1
            
            # Display iteration results
            rprint(Panel(
                Markdown(current_code),
                title=f"Implementation Result - Iteration {iterations}",
                border_style="green"
            ))
            
        result = {
            "code": current_code,
            "iterations": iterations,
            "task_id": task["id"],
            "final_goal": improvement_goals[iterations - 1]
        }
        
        rprint(Panel.fit(
            f"""✅ Implementation Complete
            Total Iterations: {iterations}
            Final Goal Achieved: {improvement_goals[iterations - 1]}""",
            title="Task Complete"
        ))
        return result
        
    def modify_code(
        self,
        code: str,
        feedback: Dict[str, Any],
        task: Dict[str, Any]
    ) -> str:
        """
        Modify code based on feedback.
        
        Args:
            code: Current code implementation
            feedback: Feedback from review
            task: Original task details
            
        Returns:
            Modified code
        """
        rprint(Panel.fit("🔄 Starting Code Modification", title="Code Update"))
        
        response = self.agent.run(
            f"""Modify this code based on feedback:
            
            Current Code:
            {code}
            
            Feedback:
            {feedback}
            
            Original Requirements:
            {task['requirements']}
            
            Format your response in markdown with code blocks.
            Include a section explaining the improvements made.
            """
        )
        
        modified_code = str(response)
        rprint(Panel(
            Markdown(modified_code),
            title="Modified Implementation",
            border_style="blue"
        ))
        
        rprint(Panel.fit("✅ Modification Complete", title="Update Complete"))
        return modified_code

# Create singleton instance
code_agent = CodeAgent() 