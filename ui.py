import streamlit as st
from utils import parse_pdf, parse_txt

def render_sidebar():
    """
    Renders the sidebar components for Model Path and File Upload.
    Returns True if the app is ready to proceed (model path and file are set), False otherwise.
    """
    with st.sidebar:
        st.header("1. Setup (Direct Model)")
        st.markdown("""
        Download a GGUF model file from Hugging Face.
        We recommend **Phi-3-mini-4k-instruct-q4.gguf**.
        
        [Click here to download it](https://huggingface.co/microsoft/Phi-3-mini-4k-instruct-gguf/blob/main/Phi-3-mini-4k-instruct-q4.gguf)
        (Right-click the "download" button and "Save Link As...")
        """)
        
        model_path = st.text_input("Enter the *full file path* to your .gguf model:")
        st.session_state.model_path = model_path
        
        if model_path:
            st.success("Model path set!")

        st.header("2. Upload Source")
        uploaded_file = st.file_uploader(
            "Upload your source content (.txt, .pdf)", 
            type=["txt", "pdf"]
        )
        
        if uploaded_file:
            if not st.session_state.model_path:
                st.warning("Please provide the path to your model file above.")
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
    if not st.session_state.model_path:
        st.info("Please provide the file path to your GGUF model in the sidebar.")
        return False
    
    if not st.session_state.source_text:
        st.info("Please upload your source content in the sidebar.")
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