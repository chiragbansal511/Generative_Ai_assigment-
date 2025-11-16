import streamlit as st
import utils
import ui

# --- Page Configuration and Title ---
st.set_page_config(
    page_title="EduContent Seasoned (Offline)",
    page_icon="🎓",
    layout="wide"
)
st.title("🎓 EduContent Seasoned (Offline Edition)")
st.markdown("Your AI-powered assistant for creating structured learning content from a single source.")

# --- Initialize Session State ---
utils.init_session_state()

# --- Render Sidebar and Check Readiness ---
# This function handles Ollama connection, model selection, and file upload
app_ready = ui.render_sidebar()

if app_ready:
    # --- Main App Logic ---
    model_name = st.session_state.ollama_model_name  # Use the selected model name
    source_text = st.session_state.source_text
    
    col1, col2 = st.columns([1, 1])

    # --- Column 1: Roadmap Generation and Selection ---
    with col1:
        st.header("Learning Roadmap")
        
        if st.button("Generate Learning Roadmap", type="primary"):
            # Reset state for a new generation
            st.session_state.roadmap_nodes = []
            st.session_state.roadmap_dot = None
            st.session_state.selected_node_label = None
            st.session_state.selected_node_content = None
            st.session_state.assignment = None
            
            with st.spinner(f"AI ({model_name}) is analyzing your content..."):
                prompt = f"""
                Analyze the following source text and generate a hierarchical learning roadmap.
                The roadmap should identify the main topics, sub-topics, and specific concepts.
                
                Format the output *only* as a nested markdown list. 
                Use 2 spaces for each level of indentation.
                Do not include any other text or explanation.

                Example:
                - Main Topic 1
                  - Sub-Topic 1.1
                    - Concept 1.1.1
                  - Sub-Topic 1.2
                - Main Topic 2
                  - Sub-Topic 2.1

                Here is the source text:
                ---
                {source_text}
                ---
                """
                # Call the new Ollama function
                response_text = utils.call_ollama_api(model_name, prompt)
                
                if response_text:
                    nodes, dot_string = utils.parse_roadmap_to_dot(response_text)
                    st.session_state.roadmap_nodes = nodes
                    st.session_state.roadmap_dot = dot_string
                else:
                    st.error("AI failed to generate a roadmap.")

        # Display the visual flowchart
        if st.session_state.roadmap_dot:
            ui.render_roadmap_visual(st.session_state.roadmap_dot)
            
        # Display the interactive node buttons and capture clicks
        if st.session_state.roadmap_nodes:
            clicked_label = ui.render_node_selection(st.session_state.roadmap_nodes)
            if clicked_label:
                st.session_state.selected_node_label = clicked_label
                st.session_state.selected_node_content = None
                st.session_state.assignment = None
                st.rerun()

    # --- Column 2: Content Generation and Assignment ---
    with col2:
        # Check if a node is selected AND content hasn't been generated yet
        if st.session_state.selected_node_label and not st.session_state.selected_node_content:
            st.header(f"Content for: {st.session_state.selected_node_label}")
            with st.spinner(f"AI ({model_name}) is generating content..."):
                prompt = f"""
                Based *only* on the following source text, generate a detailed explanation
                for the specific topic: "{st.session_state.selected_node_label}".
                
                Use markdown for formatting (headings, lists, bold text).
                Ensure the explanation is clear, concise, and factually grounded *only* in the source text.

                SOURCE TEXT:
                ---
                {source_text}
                ---
                """
                # Call the new Ollama function
                response_text = utils.call_ollama_api(model_name, prompt)
                if response_text:
                    st.session_state.selected_node_content = response_text
                    st.rerun() 
                else:
                    st.error("AI failed to generate content for this node.")

        # Display the generated content if it exists
        if st.session_state.selected_node_content:
            ui.render_node_content(
                st.session_state.selected_node_label, 
                st.session_state.selected_node_content
            )
            
            # Assignment Generation
            if st.button("Generate Assignment", key=f"assign_{st.session_state.selected_node_label}"):
                with st.spinner(f"AI ({model_name}) is generating an assignment..."):
                    prompt = f"""
                    Based *only* on the following detailed text, create a short 3-question
                    multiple-choice quiz. 
                    
                    For each question, provide the question, three options (A, B, C),
                    and clearly state the correct answer.
                    Format it clearly using markdown.

                    DETAILED TEXT:
                    ---
                    {st.session_state.selected_node_content}
                    ---
                    """
                    # Call the new Ollama function
                    response_text = utils.call_ollama_api(model_name, prompt)
                    if response_text:
                        st.session_state.assignment = response_text
                    else:
                        st.error("AI failed to generate an assignment.")

            # Display the assignment if it exists
            if st.session_state.assignment:
                ui.render_assignment(st.session_state.assignment)