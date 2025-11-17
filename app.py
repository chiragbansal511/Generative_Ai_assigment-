import streamlit as st
import utils
import ui

# --- Page Configuration and Title ---
st.set_page_config(
    page_title="EduContent Seasoned (Llama)",
    page_icon="🎓",
    layout="wide"
)
st.title("🎓 EduContent Seasoned (Your Llama Edition)")
st.markdown("Your fully-automated assistant for creating structured learning content.")

# --- Initialize Session State ---
utils.init_session_state()

# --- Render Sidebar ---
# The sidebar now handles setting st.session_state.model_path
# and st.session_state.source_text
ui.render_sidebar()

# --- Model Loading (Loads your Llama model) ---
if st.session_state.model_path and not st.session_state.llm_model:
    with st.spinner(f"Loading your Llama model from '{st.session_state.model_path}'..."):
        st.session_state.llm_model = utils.load_model(st.session_state.model_path)
        if st.session_state.llm_model:
            st.success("Llama model loaded successfully!")

# --- Main App Logic ---
# Check if the model is loaded first
if not st.session_state.llm_model:
    st.info("Please provide the file path to your Llama GGUF model in the sidebar.")
    st.stop()

# If model is loaded, check if source text is ready
if not st.session_state.source_text:
    st.info("Please provide a source (file, text, or URL) in the sidebar and click 'Process Source'.")
    st.stop()

# --- If both Model and Source are ready, run the app ---
model = st.session_state.llm_model
source_text = st.session_state.source_text

col1, col2 = st.columns([1, 1])

# --- Column 1: Roadmap Generation and Selection ---
with col1:
    st.header("Learning Roadmap")
    
    if st.button("Generate Learning Roadmap", type="primary"):
        st.session_state.roadmap_nodes = []
        st.session_state.roadmap_dot = None
        st.session_state.selected_node_label = None
        st.session_state.selected_node_content = None
        st.session_state.assignment = None
        
        with st.spinner("Your Llama is analyzing the content..."):
            prompt = f"""
            Analyze the following source text and generate a hierarchical learning roadmap.
            Format the output *only* as a nested markdown list. 
            Use 2 spaces for each level of indentation.
            Do not include any other text or explanation.

            Example:
            - Main Topic 1
              - Sub-Topic 1.1
            - Main Topic 2

            Source Text:
            ---
            {source_text}
            ---
            """
            response_text = utils.call_model_api(model, prompt)
            
            if response_text:
                nodes, dot_string = utils.parse_roadmap_to_dot(response_text)
                st.session_state.roadmap_nodes = nodes
                st.session_state.roadmap_dot = dot_string
            else:
                st.error("AI failed to generate a roadmap.")

    if st.session_state.roadmap_dot:
        ui.render_roadmap_visual(st.session_state.roadmap_dot)
        
    if st.session_state.roadmap_nodes:
        clicked_label = ui.render_node_selection(st.session_state.roadmap_nodes)
        if clicked_label:
            st.session_state.selected_node_label = clicked_label
            st.session_state.selected_node_content = None
            st.session_state.assignment = None
            st.rerun()

# --- Column 2: Content Generation and Assignment ---
with col2:
    if st.session_state.selected_node_label and not st.session_state.selected_node_content:
        st.header(f"Content for: {st.session_state.selected_node_label}")
        with st.spinner(f"Your Llama is generating content for '{st.session_state.selected_node_label}'..."):
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
            response_text = utils.call_model_api(model, prompt)
            if response_text:
                st.session_state.selected_node_content = response_text
                st.rerun() 
            else:
                st.error("AI failed to generate content for this node.")

    if st.session_state.selected_node_content:
        ui.render_node_content(
            st.session_state.selected_node_label, 
            st.session_state.selected_node_content
        )
        
        if st.button("Generate Assignment", key=f"assign_{st.session_state.selected_node_label}"):
            with st.spinner("Your Llama is generating an assignment..."):
                prompt = f"""
                Based *only* on the following detailed text, create a short 3-question
                multiple-choice quiz with a correct answer key.
                Format it clearly using markdown.
                DETAILED TEXT:
                ---
                {st.session_state.selected_node_content}
                ---
                """
                response_text = utils.call_model_api(model, prompt)
                if response_text:
                    st.session_state.assignment = response_text
                else:
                    st.error("AI failed to generate an assignment.")

        if st.session_state.assignment:
            ui.render_assignment(st.session_state.assignment)