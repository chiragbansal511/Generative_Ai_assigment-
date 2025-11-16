import streamlit as st
import ollama
import time
import re
import io
import pypdf

# --- Ollama Configuration ---
def check_ollama_connection():
    """Checks if the Ollama service is running and returns available models."""
    try:
        models = ollama.list()
        return models['models']
    except Exception as e:
        st.error(f"Ollama connection error: {e}")
        st.error("Please make sure Ollama is running on your machine.")
        return None

def call_ollama_api(model_name, prompt, max_retries=3):
    """Calls the local Ollama API with a simple retry logic."""
    delay = 1
    for i in range(max_retries):
        try:
            # Use ollama.chat for instruction-following models
            response = ollama.chat(
                model=model_name,
                messages=[{'role': 'user', 'content': prompt}]
            )
            return response['message']['content']
        except Exception as e:
            st.warning(f"Error calling Ollama: {e}. Retrying in {delay}s...")
            time.sleep(delay)
            delay *= 2
    
    st.error(f"Failed to get a response from Ollama model '{model_name}' after {max_retries} retries.")
    st.error("Please ensure Ollama is running and the model is downloaded (e.g., 'ollama pull phi3').")
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

# --- Session State Initialization (Modified) ---
def init_session_state():
    """Initializes session state variables."""
    defaults = {
        "source_text": None,
        "roadmap_nodes": [],
        "roadmap_dot": None,
        "selected_node_label": None,
        "selected_node_content": None,
        "assignment": None,
        "ollama_model_name": None,  # Replaces gemini_model
        "available_models": []
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value