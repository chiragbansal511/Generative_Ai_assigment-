import streamlit as st
import time
import re
import io
import pypdf
from ctransformers import AutoModelForCausalLM

# --- Model Loading (NEW) ---

@st.cache_resource
def load_model(model_path):
    """
    Loads the GGUF model from the given file path.
    We cache this so it only loads once per session.
    """
    if not model_path:
        return None
    try:
        # model_type="phi-3" is more specific and better if we recommend Phi-3
        llm = AutoModelForCausalLM.from_pretrained(model_path, model_type="phi-3")
        return llm
    except Exception as e:
        st.error(f"Error loading model from path '{model_path}': {e}")
        st.error("Please ensure the file path is correct and you have downloaded a compatible GGUF model.")
        return None

def call_model_api(llm, prompt):
    """
    Calls the loaded CTransformer model with a specific chat template.
    """
    if not llm:
        st.error("Model is not loaded.")
        return None
    
    try:
        # We must format the prompt using the model's expected chat template.
        # For Phi-3, the template is: <|user|>\n{prompt}<|end|>\n<|assistant|>
        formatted_prompt = f"<|user|>\n{prompt}<|end|>\n<|assistant|>"
        
        # Generate the response
        response = llm(formatted_prompt, stream=False, max_new_tokens=4096)
        return response
    except Exception as e:
        st.error(f"Error during model generation: {e}")
        return None

# --- PDF and Text Parsing (No changes) ---
def parse_pdf(file_bytes):
    """Extracts text from an uploaded PDF file."""
    try:
        pdf_file = io.BytesIO(file_bytes)
        pdf_reader = pypdf.PdfReader(pdf_file)
        text = ""
        for page in pdf_reader.pages:
            text += page.extract_text()
        return text
    except Exception as e:
        st.error(f"Error parsing PDF: {e}")
        return None

def parse_txt(file_bytes):
    """Extracts text from an uploaded TXT file."""
    try:
        return file_bytes.decode("utf-8")
    except Exception as e:
        st.error(f"Error parsing TXT file: {e}")
        return None

# --- Roadmap Parsing (No changes) ---
def parse_roadmap_to_dot(markdown_text):
    """
    Parses a nested markdown list and generates a Graphviz DOT string
    and a list of node tuples (level, label).
    """
    if not markdown_text:
        return [], ""
        
    nodes = []
    dot_edges = []
    dot_nodes = set()
    parent_stack = []
    
    for line in markdown_text.split('\n'):
        match = re.match(r'^(\s*)[-*]\s(.*)', line)
        if match:
            indentation = len(match.group(1))
            label = match.group(2).strip()
            level = indentation // 2  # Assuming 2 spaces per indent level
            
            nodes.append((level, label))
            
            node_name = f'"{label}"' # Quote to handle special characters
            
            while len(parent_stack) > level:
                parent_stack.pop()
                
            if parent_stack:
                parent_label = parent_stack[-1]
                parent_name = f'"{parent_label}"'
                dot_edges.append(f'{parent_name} -> {node_name};')
            else:
                dot_nodes.add(f'{node_name};')
            
            parent_stack.append(label)

    dot_string = "digraph G {\n"
    dot_string += "  node [shape=box, style=rounded, fontname=Inter, fillcolor=\"#E6F7FF\", style=filled];\n"
    dot_string += "  edge [fontname=Inter];\n"
    dot_string += "  rankdir=LR;\n" # Left-to-Right layout
    dot_string += "  " + "\n  ".join(list(dot_nodes)) + "\n"
    dot_string += "  " + "\n  ".join(dot_edges) + "\n"
    dot_string += "}"
    
    return nodes, dot_string

# --- Session State Initialization (Updated) ---
def init_session_state():
    """Initializes session state variables."""
    defaults = {
        "source_text": None,
        "roadmap_nodes": [],
        "roadmap_dot": None,
        "selected_node_label": None,
        "selected_node_content": None,
        "assignment": None,
        "model_path": None,  # NEW: Path to the GGUF file
        "llm_model": None    # NEW: The loaded model object
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value