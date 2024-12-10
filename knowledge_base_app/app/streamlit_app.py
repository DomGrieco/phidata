import streamlit as st
from typing import Dict, Any, Optional
import logging
from pathlib import Path
import json

from app.agents.documentation_agent import DocumentationAgent
from app.config import get_settings
from phi.document import Document

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize settings
settings = get_settings()

def initialize_agent() -> DocumentationAgent:
    """Initialize the Documentation Agent"""
    if 'doc_agent' not in st.session_state:
        logger.info("Initializing DocumentationAgent...")
        st.session_state.doc_agent = DocumentationAgent()
    return st.session_state.doc_agent

def display_stats(stats: Dict[str, Any]):
    """Display knowledge base statistics"""
    if stats["status"] == "success":
        st.sidebar.metric("Total Documents", stats["stats"]["total_documents"])
        col1, col2 = st.sidebar.columns(2)
        with col1:
            st.metric("PDF Documents", stats["stats"]["pdf_documents"])
        with col2:
            st.metric("Text Documents", stats["stats"]["text_documents"])
    else:
        st.sidebar.error(f"Error getting statistics: {stats['message']}")

def format_source_info(source: Document) -> str:
    """Format source information for display in a concise way"""
    try:
        name = source.name or "Unknown Document"
        meta_data = source.meta_data or {}
        section = meta_data.get("section")
        page = meta_data.get("page")
        
        parts = [f"📄 **{name}**"]
        if section and section != "General":
            parts.append(f"(Section: {section})")
        if page:
            parts.append(f"(Page {page})")
        return " ".join(parts)
    except Exception as e:
        logger.warning(f"Error formatting source info: {str(e)}")
        return "📄 Unknown Source"

def get_document_path(source: Document) -> Optional[str]:
    """Get the document path from source metadata"""
    try:
        name = source.name
        if not name:
            return None
            
        # Check in both PDF and text directories
        pdf_path = Path("data/pdfs") / name
        text_path = Path("data/text") / name
        
        if pdf_path.exists():
            return str(pdf_path)
        if text_path.exists():
            return str(text_path)
        return None
    except Exception as e:
        logger.warning(f"Error getting document path: {str(e)}")
        return None

def main():
    # Set page config
    st.set_page_config(
        page_title="Documentation Assistant",
        page_icon="📚",
        layout="wide",
    )

    # Header
    st.title("📚 Documentation Assistant")
    st.markdown("""
    Ask questions about your documentation and get instant answers!
    The assistant searches through your knowledge base and provides relevant information.
    """)

    # Initialize agent
    doc_agent = initialize_agent()

    # Sidebar with stats
    st.sidebar.title("Knowledge Base Stats")
    stats = doc_agent.get_stats()
    display_stats(stats)

    # Main query interface
    query = st.text_input(
        "Ask a question about your documentation:",
        placeholder="E.g., How does feature X work?",
        key="query_input"
    )

    if query:
        # Create placeholder for response
        response_placeholder = st.empty()
        sources_placeholder = st.empty()
        
        with st.spinner("Searching documentation..."):
            try:
                # Process query
                response = doc_agent.query(query)
                
                if response["status"] == "success":
                    # Display response in placeholder
                    response_placeholder.markdown("### Answer")
                    response_placeholder.markdown(response["response"])
                    
                    # Display document usage information
                    metadata = response["metadata"]
                    st.info(f"""
                    📊 **Document Usage:**
                    - Total relevant documents found: {metadata.get('total_relevant_docs', 0)}
                    - Documents used in response: {metadata.get('used_docs', 0)}
                    """)
                    
                    # Display sources if available
                    sources = metadata.get("sources", [])
                    if sources:
                        with sources_placeholder.expander("📑 Source Documents", expanded=True):
                            st.markdown("### Referenced Documentation")
                            st.markdown("The following documents were used to generate this response:")
                            
                            for idx, source in enumerate(sources, 1):
                                col1, col2 = st.columns([4, 1])
                                with col1:
                                    st.markdown(format_source_info(source))
                                with col2:
                                    doc_path = get_document_path(source)
                                    if doc_path:
                                        with open(doc_path, "rb") as f:
                                            st.download_button(
                                                "📥 Download",
                                                f,
                                                file_name=source.name or "document",
                                                mime="application/octet-stream",
                                                key=f"download_{idx}"
                                            )
                                if idx < len(sources):
                                    st.markdown("---")
                    else:
                        st.warning("⚠️ No source documents were referenced in generating this response.")
                else:
                    response_placeholder.error(f"Error: {response['message']}")
                    
            except Exception as e:
                logger.error(f"Error processing query: {str(e)}", exc_info=True)
                response_placeholder.error(f"An error occurred: {str(e)}")

    # Additional features in sidebar
    st.sidebar.markdown("---")
    st.sidebar.markdown("### Options")
    
    # Add refresh button for stats
    if st.sidebar.button("🔄 Refresh Stats"):
        stats = doc_agent.get_stats()
        display_stats(stats)
        st.sidebar.success("Statistics refreshed!")

    # Footer
    st.sidebar.markdown("---")
    st.sidebar.markdown("""
    ### About
    This interface allows you to interact with your documentation using natural language queries.
    The system uses advanced AI to understand your questions and provide relevant answers from your knowledge base.
    """)

if __name__ == "__main__":
    main() 