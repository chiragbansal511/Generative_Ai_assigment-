import streamlit as st
import utils

def render_sidebar():
    """
    Renders the sidebar components for providing model path and source content.
    """
    with st.sidebar:
        st.header("1. Load Your Llama Model")
        st.markdown("Enter the *full file path* to your Llama `.gguf` model file.")
        
        model_path = st.text_input(
            "Model File Path:", 
            key="model_path",
            label_visibility="collapsed"
        )
        
        if model_path:
            st.success("Model path set!")

        st.divider()

        st.header("2. Provide Source Content")
        st.markdown("Choose one method to provide your content.")
        
        tab_file, tab_text, tab_url = st.tabs(["File Upload", "Paste Text", "From URL"])

        with tab_file:
            uploaded_file = st.file_uploader(
                "Upload your source (.txt, .pdf)", 
                type=["txt", "pdf"],
                label_visibility="collapsed"
            )

        with tab_text:
            pasted_text = st.text_area("Paste your full text content here:", height=250)
            
        with tab_url:
            url_input = st.text_input("Enter a public URL (e.g., Wikipedia, blog post):")

        if st.button("Process Source", type="primary"):
            # Reset all content first
            st.session_state.source_text = None
            st.session_state.roadmap_nodes = []
            st.session_state.roadmap_dot = None
            st.session_state.selected_node_label = None
            st.session_state.selected_node_content = None
            st.session_state.assignment = None
            
            with st.spinner("Processing source..."):
                if uploaded_file:
                    file_bytes = uploaded_file.getvalue()
                    if uploaded_file.type == "application/pdf":
                        st.session_state.source_text = utils.parse_pdf(file_bytes)
                    else:
                        st.session_state.source_text = utils.parse_txt(file_bytes)
                
                elif pasted_text:
                    st.session_state.source_text = pasted_text
                
                elif url_input:
                    st.session_state.source_text = utils.fetch_url_content(url_input)
                
                else:
                    st.warning("Please provide a source (file, text, or URL).")
            
            if st.session_state.source_text:
                st.success("Source processed!")
                with st.expander("Show source text preview"):
                    st.text(st.session_state.source_text[:500] + "...")
            else:
                st.error("Could not process the source.")
            
            st.rerun()

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