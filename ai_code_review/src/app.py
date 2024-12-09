import streamlit as st
from phi.assistant import Assistant
from code_review_agent import CodeReviewAgent

# Initialize the code review agent
review_agent = CodeReviewAgent()

# Create an assistant with the review agent
assistant = Assistant(
    name="Code Review Assistant",
    description=(
        "I am a code review assistant that helps analyze your code for security, "
        "performance, and style issues. Simply paste your code and I'll provide "
        "a comprehensive review."
    ),
    agent=review_agent
)

# Set up the Streamlit page
st.set_page_config(
    page_title="Code Review Assistant",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Custom CSS to ensure proper text formatting and styling
st.markdown("""
    <style>
        /* Base text styles */
        .stMarkdown {
            white-space: normal !important;
        }
        .review-text {
            line-height: 1.4;
            margin-bottom: 0.8rem;
            font-size: 0.95rem;
            color: #E0E0E0 !important;
        }
        
        /* Header styles */
        .main-title {
            color: #2196F3 !important;
            font-size: 1.4rem !important;
            margin-bottom: 1rem !important;
            font-weight: 600 !important;
        }
        
        /* Section styles */
        .section-header {
            color: #90CAF9 !important;
            font-size: 1.1rem !important;
            margin-top: 1.2rem !important;
            margin-bottom: 0.8rem !important;
            font-weight: 500 !important;
        }
        
        /* Category headers */
        .category-header {
            color: #64B5F6 !important;
            font-size: 1rem !important;
            margin-top: 0.8rem !important;
            margin-bottom: 0.4rem !important;
            font-weight: 500 !important;
        }
        
        /* Code elements */
        code {
            color: #81C784 !important;
            background-color: rgba(129, 199, 132, 0.1) !important;
            padding: 0.1rem 0.3rem !important;
            border-radius: 3px !important;
            font-family: 'Courier New', Courier, monospace !important;
        }
        
        /* Bullet points */
        .bullet-point {
            margin-left: 1rem;
            margin-bottom: 0.6rem;
            color: #E0E0E0 !important;
        }
        
        /* Layout */
        .main {
            max-width: 1200px;
            padding: 1rem 2rem;
        }
        
        /* Input area */
        .stTextArea textarea {
            font-family: 'Courier New', Courier, monospace !important;
            background-color: #1E1E1E !important;
            color: #E0E0E0 !important;
        }
        
        /* Success/warning messages */
        .stSuccess, .stWarning {
            padding: 0.5rem 1rem !important;
            border-radius: 4px !important;
        }
    </style>
""", unsafe_allow_html=True)

st.title("Code Review Assistant")
st.markdown("##### Built using [phidata](https://github.com/phidatahq/phidata)")

# Add instructions
with st.expander("ℹ️ How to use"):
    st.markdown("""
    1. Paste your code in the text area below
    2. Click 'Review Code' to get a comprehensive analysis
    3. The review will cover:
        - Security vulnerabilities
        - Performance optimizations
        - Code style and best practices
    """)

# Create the code input area at the top
code = st.text_area("Paste your code here:", height=200)
review_button = st.button("Review Code")

# Display review results below the input
if review_button:
    if code:
        st.markdown("---")
        st.markdown('<div class="main-title">Review Results</div>', unsafe_allow_html=True)
        
        with st.spinner("Analyzing code..."):
            # Collect the full response first
            full_response = ""
            for chunk in assistant.run(code):
                full_response += chunk if isinstance(chunk, str) else str(chunk)
            
            # Process the complete response
            sections = full_response.split("\n")
            current_section = []
            
            for line in sections:
                line = line.strip()
                if line:
                    if line.startswith("###"):
                        # Output accumulated section if exists
                        if current_section:
                            st.markdown('<div class="review-text">' + " ".join(current_section) + '</div>', unsafe_allow_html=True)
                            current_section = []
                        # Output section header
                        header_text = line.replace("###", "").strip()
                        st.markdown(f'<div class="section-header">{header_text}</div>', unsafe_allow_html=True)
                    elif line.startswith(("1.", "2.", "3.", "4.", "5.")):
                        # Output accumulated section if exists
                        if current_section:
                            st.markdown('<div class="review-text">' + " ".join(current_section) + '</div>', unsafe_allow_html=True)
                            current_section = []
                        # Output numbered item
                        st.markdown(f'<div class="bullet-point">{line}</div>', unsafe_allow_html=True)
                    elif line.startswith(("-", "•", "*")):
                        # Output accumulated section if exists
                        if current_section:
                            st.markdown('<div class="review-text">' + " ".join(current_section) + '</div>', unsafe_allow_html=True)
                            current_section = []
                        # Output bullet point
                        st.markdown(f'<div class="bullet-point">{line}</div>', unsafe_allow_html=True)
                    elif line.startswith(("Security:", "Performance:", "Style:", "Critical:", "Recommendations:")):
                        # Output accumulated section if exists
                        if current_section:
                            st.markdown('<div class="review-text">' + " ".join(current_section) + '</div>', unsafe_allow_html=True)
                            current_section = []
                        # Output category header
                        st.markdown(f'<div class="category-header">{line}</div>', unsafe_allow_html=True)
                    else:
                        # Accumulate regular text
                        current_section.append(line)
            
            # Output any remaining text
            if current_section:
                st.markdown('<div class="review-text">' + " ".join(current_section) + '</div>', unsafe_allow_html=True)
        
        st.success("Review complete!")
    else:
        st.warning("Please paste some code to review.")