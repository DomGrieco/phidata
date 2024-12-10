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

def format_document_info(doc: Any) -> str:
    """Format document information for display"""
    try:
        # If doc is a string containing JSON or dict-like data
        if isinstance(doc, str):
            try:
                doc_data = json.loads(doc)
            except json.JSONDecodeError:
                return f"📄 {doc}"
        else:
            doc_data = doc

        # Extract meaningful information
        if isinstance(doc_data, dict):
            doc_info = []
            
            # Get document name/path
            if "name" in doc_data:
                doc_info.append(f"📄 **Document:** {doc_data['name']}")
            elif "file_path" in doc_data:
                name = Path(doc_data['file_path']).name
                doc_info.append(f"📄 **Document:** {name}")
                
            # Get section/page info
            if "page" in doc_data:
                doc_info.append(f"📃 **Page:** {doc_data['page']}")
            if "section" in doc_data:
                doc_info.append(f"📌 **Section:** {doc_data['section']}")
                
            # Get relevance score if available
            if "score" in doc_data:
                score = float(doc_data['score'])
                doc_info.append(f"🎯 **Relevance:** {score:.2f}")
                
            # Get content preview if available
            if "content" in doc_data:
                content = doc_data['content']
                if isinstance(content, str):
                    preview = content[:200] + "..." if len(content) > 200 else content
                    doc_info.append(f"📝 **Preview:** {preview}")
            
            return "\n\n".join(doc_info)
        return f"📄 {str(doc)}"
    except Exception as e:
        logger.warning(f"Error formatting document info: {str(e)}")
        return f"📄 {str(doc)}"

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
        with st.spinner("Searching documentation..."):
            try:
                # Process query
                response = doc_agent.query(query)
                
                if response["status"] == "success":
                    # Display response
                    st.markdown("### Answer")
                    st.markdown(response["response"])
                    
                    # Display relevant documents
                    if response["relevant_documents"]:
                        with st.expander("📑 Source Documents", expanded=True):
                            st.markdown("The following documents were used to generate this response:")
                            for idx, doc in enumerate(response["relevant_documents"], 1):
                                with st.container():
                                    st.markdown(f"### Source {idx}")
                                    st.markdown(format_document_info(doc))
                                    st.markdown("---")
                else:
                    st.error(f"Error: {response['message']}")
                    
            except Exception as e:
                logger.error(f"Error processing query: {str(e)}", exc_info=True)
                st.error(f"An error occurred: {str(e)}")

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