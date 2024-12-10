import typer
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from pathlib import Path

from phi.vectordb.pgvector import PgVector
from phi.embedder.openai import OpenAIEmbedder

from app.config import get_settings
from app.utils.document_processor import DocumentProcessor

# Initialize settings and console
settings = get_settings()
console = Console()

def create_vector_db() -> PgVector:
    """Create and initialize vector database"""
    return PgVector(
        table_name=settings.vector_db_table,
        db_url=settings.db_url,
        embedder=OpenAIEmbedder(
            model=settings.embeddings_model,
            dimensions=settings.embeddings_dimensions,
        ),
    )

def main(
    pdf_path: str = "data/pdfs",
    text_path: str = "data/text",
    clear_existing: bool = False,
):
    """
    Ingest documents into the knowledge base
    
    Args:
        pdf_path: Path to PDF documents
        text_path: Path to text documents
        clear_existing: Whether to clear existing documents before ingestion
    """
    
    # Create vector database
    vector_db = create_vector_db()
    processor = DocumentProcessor(vector_db)
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        # Clear existing documents if requested
        if clear_existing:
            progress.add_task("Clearing existing documents...", total=None)
            result = processor.clear_knowledge_base()
            console.print(Panel(f"[bold]{result['message']}[/bold]"))
        
        # Process PDFs
        if Path(pdf_path).exists():
            progress.add_task("Processing PDF documents...", total=None)
            result = processor.ingest_pdfs(pdf_path)
            console.print(Panel(f"[bold]{result['message']}[/bold]"))
        
        # Process text documents
        if Path(text_path).exists():
            progress.add_task("Processing text documents...", total=None)
            result = processor.ingest_text(text_path)
            console.print(Panel(f"[bold]{result['message']}[/bold]"))
        
        # Show document counts
        doc_counts = processor.get_document_count()
        console.print(Panel(
            "[bold green]Document Count Summary:[/bold green]\n" +
            f"PDF Documents: {doc_counts['pdf_documents']}\n" +
            f"Text Documents: {doc_counts['text_documents']}\n" +
            f"Total Documents: {doc_counts['total']}"
        ))

if __name__ == "__main__":
    typer.run(main) 