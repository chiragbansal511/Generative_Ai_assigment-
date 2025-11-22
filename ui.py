import streamlit as st
import utils

def render_sidebar():
    """
    Renders the sidebar components for API Key and source content.
    """
    with st.sidebar:
        st.header("1. Google AI Setup")
        
        api_key = st.text_input(
            "Enter Google AI Studio API Key:", 
            type="password",
            help="Get your key from https://aistudio.google.com/"
        )
        
        if api_key:
            # Only configure if the key has changed or model isn't set
            if api_key != st.session_state.gemini_api_key:
                model = utils.configure_gemini(api_key)
                if model:
                    st.session_state.gemini_api_key = api_key
                    st.session_state.gemini_model = model
                    st.success("Gemini Configured!")

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
        # FIX: enumerate adds a unique index 'i' to prevent duplicate keys
        for i, (level, label) in enumerate(nodes):
            indent = "• " * level
            # Key is now f"btn_{i}_{label}" making it unique even if label repeats
            if st.button(f"{indent}{label}", key=f"btn_{i}_{label}"):
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