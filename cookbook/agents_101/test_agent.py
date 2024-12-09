import typer
from typing import Optional, List, Dict
from phi.agent import Agent
from phi.storage.agent.sqlite import SqlAgentStorage
from phi.tools.file import FileTools
from phi.workflow import Workflow
from phi.workflow.workflow import WorkflowRun, RunResponse
from phi.memory.workflow import WorkflowMemory
from phi.knowledge.text import TextKnowledgeBase
from phi.knowledge.combined import CombinedKnowledgeBase
from phi.vectordb.pgvector import PgVector, SearchType
from phi.model.openai import OpenAIChat
import os
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.sql import text

# Configuration
MAX_ITERATIONS = 1  # Easily adjust this for testing

# Add helper functions for document operations
def get_file_content(file_path: str, default_content: str = "") -> str:
    """Get file content, creating file with default content if it doesn't exist"""
    full_path = base_dir / file_path
    if not full_path.exists():
        full_path.parent.mkdir(parents=True, exist_ok=True)
        full_path.write_text(default_content)
        if os.name == 'nt':  # Windows
            os.chmod(full_path, stat.S_IRUSR | stat.S_IWUSR)
        else:  # Unix-like
            os.chmod(full_path, 0o644)
    return full_path.read_text()

# Create necessary directories with proper permissions
base_dir = Path("docs").resolve()
for dir_path in ["requirements", "tasks"]:
    full_path = base_dir / dir_path
    full_path.mkdir(parents=True, exist_ok=True)
    # Ensure directory has read/write/execute permissions for the current user
    if os.name == 'nt':  # Windows
        import stat
        os.chmod(full_path, stat.S_IRUSR | stat.S_IWUSR | stat.S_IXUSR)
    else:  # Unix-like
        os.chmod(full_path, 0o755)

# Initialize required document structure
REQUIRED_DOCS = {
    "requirements/requirements.txt": "# Project Requirements\n\n",
    "requirements/risks.txt": "# Project Risks\n\n",
    "requirements/quality.txt": "# Quality Assessment\n\n",
    "tasks/README.txt": "# Project Tasks\n\nThis directory contains task lists organized by project phase.\n",
}

# Initialize document structure with proper permissions
for file_path, default_content in REQUIRED_DOCS.items():
    full_path = base_dir / file_path
    if not full_path.exists():
        full_path.parent.mkdir(parents=True, exist_ok=True)
        full_path.write_text(default_content)
        # Set read/write permissions for files
        if os.name == 'nt':  # Windows
            os.chmod(full_path, stat.S_IRUSR | stat.S_IWUSR)
        else:  # Unix-like
            os.chmod(full_path, 0o644)

# Database connection for memory storage and knowledge base
DB_URL = "postgresql+psycopg://ai:ai@localhost:5532/ai"

# Step 1: Define Knowledge Bases for different types of project documentation
requirements_kb = TextKnowledgeBase(
    path=Path("docs/requirements").resolve(),
    vector_db=PgVector(
        table_name="requirements_docs",
        db_url=DB_URL,
        search_type=SearchType.hybrid
    ),
    formats=[".txt"]
)

tasks_kb = TextKnowledgeBase(
    path=Path("docs/tasks").resolve(),
    vector_db=PgVector(
        table_name="tasks_docs",
        db_url=DB_URL,
        search_type=SearchType.hybrid
    ),
    formats=[".txt"]
)

# Combined knowledge base for comprehensive context
knowledge_base = CombinedKnowledgeBase(
    sources=[requirements_kb, tasks_kb],
    vector_db=PgVector(
        table_name="project_documents",
        db_url=DB_URL
    ),
)

# Step 2: Memory Storage Configuration
memory = SqlAgentStorage(
    table_name="project_memory",
    db_file="tmp/project_memory.db"
)

# Step 3: Tools Configuration
file_tool = FileTools(
    base_dir=Path("docs").resolve(),
    save_files=True,
    read_files=True,
    list_files=True
)

# Step 4: Define Agents with Enhanced Roles
planner_agent = Agent(
    name="Project Planner",
    role="Strategic project planning and task management specialist",
    model=OpenAIChat(id="gpt-4o"),
    instructions=[
        "Create and maintain project documentation",
        "Break down high-level objectives into actionable tasks:",
        "1. First analyze requirements from requirements/requirements.txt",
        "2. For each identified phase, create a task file in tasks/ directory",
        "3. Task files should be named: tasks/{phase}_tasks.txt",
        "For each task list, include:",
        "  - Clear task descriptions",
        "  - Priority levels",
        "  - Dependencies",
        "  - Estimated effort",
        "  - Acceptance criteria",
        "Use the knowledge base to maintain context across iterations",
        "Store important decisions and context in memory",
    ],
    tools=[file_tool],
    storage=memory,
    knowledge_base=knowledge_base,
    show_tool_calls=True,
    markdown=True,
)

analyst_agent = Agent(
    name="Requirements Analyst",
    role="Project requirements and risk analysis specialist",
    model=OpenAIChat(id="gpt-4o"),
    instructions=[
        "Review and analyze project requirements",
        "Document requirements in requirements/requirements.txt",
        "Identify and document potential risks in requirements/risks.txt",
        "Ensure requirements are SMART",
        "Maintain a risk register and mitigation strategies",
        "Use the knowledge base to maintain context",
        "Store analysis results and decisions in memory",
    ],
    tools=[file_tool],
    storage=memory,
    knowledge_base=knowledge_base,
    show_tool_calls=True,
    markdown=True,
)

qa_agent = Agent(
    name="Quality Assurance",
    role="Project quality and compliance specialist",
    model=OpenAIChat(id="gpt-4o"),
    instructions=[
        "Review all project documentation for quality",
        "Validate requirements against best practices",
        "Create and maintain quality metrics",
        "Document quality findings in requirements/quality.txt",
        "Use the knowledge base for consistent evaluation",
        "Store quality assessment results in memory",
    ],
    tools=[file_tool],
    storage=memory,
    knowledge_base=knowledge_base,
    show_tool_calls=True,
    markdown=True,
)

# Step 5: Supervisor Agent
supervisor_agent = Agent(
    name="Project Supervisor",
    role="Project orchestration and oversight specialist",
    model=OpenAIChat(id="gpt-4o"),
    team=[planner_agent, analyst_agent, qa_agent],
    instructions=[
        "Coordinate the project management process",
        "Monitor all documentation in requirements/ and tasks/ directories",
        "Assign specific tasks to each team member",
        "Monitor progress and ensure quality",
        "Identify gaps and delegate work to appropriate agents",
        "Use team memory and knowledge base for decision making",
        "Store coordination decisions and progress in memory",
    ],
    storage=memory,
    knowledge_base=knowledge_base,
    show_tool_calls=True,
    markdown=True,
)

# Step 6: Workflow Implementation
class ProjectManagementWorkflow(Workflow):
    def __init__(self):
        super().__init__(
            name="project_management_workflow",
            memory=WorkflowMemory()
        )
        
    def run(self, **kwargs):
        try:
            # Initialize knowledge base with upsert=True to update existing records
            knowledge_base.load(recreate=False, upsert=True)
            
            # Get max iterations with a hard limit
            max_iterations = min(kwargs.get("max_iterations", 10), 20)
            iteration = 0
            
            # Check for existing initial requirements
            initial_req_path = "requirements/initial_requirements.txt"
            try:
                content = get_file_content(initial_req_path)
                if content.strip():
                    print("\nFound existing initial requirements. Analyzing...")
                    analysis_response = analyst_agent.run(
                        f"Read and analyze the existing requirements in {initial_req_path}. "
                        "Use this as a basis for further refinement.",
                        stream=True
                    )
                    for chunk in analysis_response:
                        print(chunk.content if hasattr(chunk, 'content') else '', end='')
                else:
                    raise FileNotFoundError("Empty initial requirements file")
            except (FileNotFoundError, IOError):
                print("\nInitializing project setup...")
                setup_response = analyst_agent.run(
                    "Create initial project requirements document in requirements/requirements.txt. "
                    "Include sections for objectives, scope, and success criteria.",
                    stream=True
                )
                for chunk in setup_response:
                    print(chunk.content if hasattr(chunk, 'content') else '', end='')
            
            while iteration < max_iterations:
                print(f"\nIteration {iteration + 1}/{max_iterations}: Refining project documentation and tasks...")
                
                try:
                    # Step 1: Analyze current state using knowledge base
                    print("\nAnalyzing current project state...")
                    analysis_task = (
                        "Review all documentation in the requirements and tasks directories. "
                        "Use the knowledge base to compare with previous iterations. "
                        "Identify gaps, inconsistencies, and areas needing improvement. "
                        "Create a status report in requirements/status.txt"
                    )
                    for chunk in supervisor_agent.run(analysis_task, stream=True):
                        print(chunk.content if hasattr(chunk, 'content') else '', end='')
                    
                    # Step 2: Update requirements with memory context
                    print("\nUpdating requirements...")
                    req_task = (
                        "Review and update requirements based on the latest analysis. "
                        "Use memory to maintain consistency with previous decisions. "
                        "Update requirements/requirements.txt"
                    )
                    for chunk in analyst_agent.run(req_task, stream=True):
                        print(chunk.content if hasattr(chunk, 'content') else '', end='')
                    
                    # Step 3: Update task lists by phase
                    print("\nUpdating task lists by project phase...")
                    task_update = (
                        "Review the requirements in requirements/requirements.txt to:\n"
                        "1. Identify the main project phases\n"
                        "2. For each phase, create or update '{phase}_tasks.txt' in the tasks directory\n"
                        "3. Ensure each task file includes:\n"
                        "   - Clear task descriptions\n"
                        "   - Priority levels\n"
                        "   - Dependencies\n"
                        "   - Estimated effort\n"
                        "   - Acceptance criteria\n"
                        "4. Remove any task files for phases no longer relevant"
                    )
                    for chunk in planner_agent.run(task_update, stream=True):
                        print(chunk.content if hasattr(chunk, 'content') else '', end='')
                    
                    # Step 4: Quality check with historical context
                    print("\nPerforming quality check...")
                    qa_task = (
                        "Review all documentation and tasks. "
                        "Use memory to compare with previous quality assessments. "
                        "Verify quality and compliance. "
                        "Document findings in requirements/quality.txt"
                    )
                    qa_response = qa_agent.run(qa_task, stream=True)
                    completion_status = {"complete": False, "gaps": []}
                    
                    for chunk in qa_response:
                        content = chunk.content if hasattr(chunk, 'content') else ''
                        print(content, end='')
                        if "NO_GAPS_FOUND" in content:
                            completion_status["complete"] = True
                        elif "GAP:" in content:
                            completion_status["gaps"].append(content.split("GAP:")[1].strip())
                    
                    # Store iteration results in memory
                    self.memory.add_run(
                        WorkflowRun(
                            input={"iteration": iteration},
                            response=RunResponse(
                                content=f"Iteration {iteration} completed",
                                event="IterationComplete",
                                metrics={
                                    "completion_status": completion_status,
                                    "timestamp": "current_timestamp"
                                }
                            )
                        )
                    )
                    
                    if completion_status["complete"]:
                        print("\nProject planning is complete! All documentation meets quality standards.")
                        break
                    elif completion_status["gaps"]:
                        print("\nIdentified gaps to address:")
                        for gap in completion_status["gaps"]:
                            print(f"- {gap}")
                    
                    # Update knowledge base with new documents
                    knowledge_base.load(recreate=False, upsert=True)
                    
                    iteration += 1
                except Exception as e:
                    print(f"\nError during iteration {iteration + 1}: {str(e)}")
                    print("Attempting to continue with next iteration...")
                    iteration += 1
                    continue
            
            if iteration == max_iterations:
                print("\nMaximum iterations reached. Please review the current state and adjust if needed.")
            
            return RunResponse(
                content="Workflow completed",
                event="WorkflowComplete",
                metrics={
                    "total_iterations": iteration,
                    "completion_status": completion_status
                }
            )
        except Exception as e:
            print(f"\nCritical workflow error: {str(e)}")
            return RunResponse(
                content=f"Workflow failed: {str(e)}",
                event="WorkflowError",
                metrics={
                    "error": str(e),
                    "iteration": iteration if 'iteration' in locals() else 0
                }
            )

workflow = ProjectManagementWorkflow()

# Step 7: Entry Point
def main(
    max_iterations: int = typer.Option(MAX_ITERATIONS, help=f"Maximum number of planning iterations (max {MAX_ITERATIONS})"),
    jira_sync: bool = typer.Option(False, help="Enable Jira synchronization"),
):
    """Run the project management workflow with specified options"""
    if jira_sync:
        print("Jira synchronization is disabled for testing")
    workflow.run(max_iterations=max_iterations)

if __name__ == "__main__":
    typer.run(main)
