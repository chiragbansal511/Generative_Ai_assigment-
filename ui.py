import streamlit as st
from utils import configure_gemini, parse_pdf, parse_txt

def render_sidebar():
    """
    Renders the sidebar components for API configuration and file upload.
    Returns True if the app is ready to proceed (API and file are set), False otherwise.
    """
    with st.sidebar:
        st.header("1. Setup")
        api_key = st.text_input("Enter your Google Gemini API Key:", type="password")
        
        if api_key and not st.session_state.gemini_model:
            model = configure_gemini(api_key)
            if model:
                st.session_state.gemini_model = model
                st.success("Gemini API Key configured!")
            else:
                st.error("Failed to configure API. Please check your key.")

        st.header("2. Upload Source")
        uploaded_file = st.file_uploader(
            "Upload your source content (.txt, .pdf)", 
            type=["txt", "pdf"]
        )
        
        if uploaded_file:
            if not st.session_state.gemini_model:
                st.warning("Please enter your Gemini API key to proceed.")
            else:
                file_bytes = uploaded_file.getvalue()
                if uploaded_file.type == "application/pdf":
                    text = parse_pdf(file_bytes)
                else:
                    text = parse_txt(file_bytes)
                
                if text:
                    st.session_state.source_text = text
                    st.success("File processed successfully!")
                    with st.expander("Show source text preview"):
                        st.text(text[:500] + "...")

    # Return status checks
    if not st.session_state.gemini_model:
        st.info("Please enter your Google Gemini API Key in the sidebar to begin.")
        return False
    
    if not st.session_state.source_text:
        st.info("Please upload your source content in the sidebar to get started.")
        return False
        
    return True

def render_roadmap_visual(dot_string):
    """Displays the Graphviz roadmap."""
    st.graphviz_chart(dot_string)

def render_node_selection(nodes):
    """
    Displays the interactive buttons for each node.
    Returns the label of the clicked node, or None.
    """
    st.subheader("Select a Node to Explore")
    clicked_label = None
    
    node_container = st.container()
    with node_container:
        for level, label in nodes:
            indent = "• " * level
            if st.button(f"{indent}{label}", key=f"btn_{label}"):
                clicked_label = label
    
    return clicked_label

def render_node_content(label, content):
    """Displays the generated content for a selected node."""
    st.header(f"Content for: {label}")
    st.markdown(content)
    st.divider()

def render_assignment(assignment_text):
    """Displays the generated assignment."""
    st.subheader("Assignment")
    st.markdown(assignment_text)