"""Example of using the Code Agent with a simple task."""

from rich import print as rprint
from rich.panel import Panel
from rich.markdown import Markdown
from ..schemas.task import TaskDefinition, TaskType, TaskPriority
from ..agents.code_agent import code_agent

def main():
    # Define a simple task
    task = TaskDefinition(
        id="TASK-001",
        type=TaskType.FEATURE,
        priority=TaskPriority.HIGH,
        description="Create a function to calculate Fibonacci numbers",
        requirements=[
            "Implement recursive and iterative solutions",
            "Add type hints",
            "Include performance comparison",
            "Add proper error handling",
            "Include docstrings and comments"
        ],
        acceptance_criteria=[
            "All test cases pass",
            "Documentation is complete",
            "Performance is optimized"
        ]
    )
    
    rprint(Panel.fit(
        f"""[bold]Task Details[/bold]
Description: {task.description}
Type: {task.type}
Priority: {task.priority}

[bold]Requirements:[/bold]
{"".join(f"• {req}\\n" for req in task.requirements)}
[bold]Acceptance Criteria:[/bold]
{"".join(f"• {crit}\\n" for crit in task.acceptance_criteria)}""",
        title="🎯 Task Definition",
        border_style="blue"
    ))
    
    # Run the implementation
    result = code_agent.implement_task(task.dict())
    
    # Display final results
    rprint(Panel(
        Markdown(result['code']),
        title="📝 Final Implementation",
        border_style="green"
    ))
    
    rprint(Panel.fit(
        f"Total Iterations: {result['iterations']}",
        title="📊 Statistics",
        border_style="cyan"
    ))

if __name__ == "__main__":
    main() 