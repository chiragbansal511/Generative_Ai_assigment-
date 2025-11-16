import streamlit as st
from utils import check_ollama_connection, parse_pdf, parse_txt

def render_sidebar():
    """
    Renders the sidebar components for Ollama configuration and file upload.
    Returns True if the app is ready to proceed (model and file are set), False otherwise.
    """
    with st.sidebar:
        st.header("1. Setup (Offline Model)")
        st.markdown("This app uses Ollama to run models locally. [Download Ollama here](https://ollama.com/).")

        if st.button("Check Ollama Connection"):
            models = check_ollama_connection()
            if models:
                st.session_state.available_models = [m['name'] for m in models]
                st.success(f"Ollama is running! Found {len(models)} models.")
            else:
                st.session_state.available_models = []
                st.error("Ollama connection failed. Is it running?")

        if st.session_state.available_models:
            selected_model = st.selectbox(
                "Select an Ollama model:",
                st.session_state.available_models
            )
            st.session_state.ollama_model_name = selected_model
        else:
            st.info("Click 'Check Connection' to find your local models. If empty, pull one with `ollama pull phi3`")

        st.header("2. Upload Source")
        uploaded_file = st.file_uploader(
            "Upload your source content (.txt, .pdf)", 
            type=["txt", "pdf"]
        )
        
        if uploaded_file:
            if not st.session_state.ollama_model_name:
                st.warning("Please connect to Ollama and select a model to proceed.")
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
    if not st.session_state.ollama_model_name:
        st.info("Please connect to Ollama and select a model in the sidebar to begin.")
        return False
    
    if not st.session_state.source_text:
        st.info("Please upload your source content in the sidebar to get started.")
        return False
        
    return True

# --- These UI functions remain unchanged ---

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