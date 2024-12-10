import streamlit as st
from typing import Dict, Any
import logging
from pathlib import Path
import json

from app.agents.documentation_agent import DocumentationAgent
from app.config import get_settings

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

def format_document_info(doc: Dict[str, Any]) -> str:
    """Format document information for display"""
    try:
        parts = []
        
        # Document name
        name = doc.get("name", "Unknown Document")
        parts.append(f"📄 **{name}**")
        
        # Section information
        section = doc.get("section")
        if section and section != "General":
            parts.append(f"📌 {section}")
        
        # Page number if available
        page = doc.get("page")
        if page:
            parts.append(f"📃 Page {page}")
        
        # Always show relevance score
        score = doc.get("relevance_score", 0.0)
        parts.append(f"🎯 Score: {score:.2f}")
        
        return " | ".join(parts)
    except Exception as e:
        logger.warning(f"Error formatting document info: {str(e)}")
        return "📄 Unknown Document"

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
                    
                    # Display relevant documents
                    if response["relevant_documents"]:
                        with sources_placeholder.expander("📑 Source Documents", expanded=True):
                            st.markdown("Referenced from (sorted by relevance):")
                            
                            # Sort documents by relevance score
                            sorted_docs = sorted(
                                response["relevant_documents"],
                                key=lambda x: x.get("relevance_score", 0),
                                reverse=True
                            )
                            
                            # Display documents with a minimum score threshold
                            for doc in sorted_docs:
                                if doc.get("relevance_score", 0) >= 0.5:  # Only show relevant matches
                                    st.markdown(format_document_info(doc))
                            
                            # Show metadata
                            st.markdown("---")
                            st.markdown(f"🎯 **Top relevance score:** {response['metadata'].get('top_score', 0):.2f}")
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