import streamlit as st
import time
import re
import io
import pypdf
import os
import requests
from bs4 import BeautifulSoup
from ctransformers import AutoModelForCausalLM

# --- Model Loading (for your Llama model) ---

@st.cache_resource
def load_model(model_path):
    """Loads your local GGUF model from the given file path."""
    if not model_path:
        return None
    
    if not os.path.exists(model_path):
        st.error(f"Error: Model file not found at path: {model_path}")
        return None
        
    try:
        # --- THIS IS THE FIX ---
        # We are now specifying the model_type as "llama"
        llm = AutoModelForCausalLM.from_pretrained(model_path, model_type="llama")
        return llm
    except Exception as e:
        st.error(f"Error loading model: {e}")
        st.error("Please ensure you have a compatible GGUF file and the correct file path.")
        return None

def call_model_api(llm, prompt):
    """Calls the loaded CTransformer model with the Llama 3 chat template."""
    if not llm:
        st.error("Model is not loaded.")
        return None
    
    try:
        # --- THIS IS THE FIX ---
        # We are using the Llama 3 Instruct chat template.
        formatted_prompt = (
            f"<|begin_of_text|><|start_header_id|>user<|end_header_id|>\n\n"
            f"{prompt}<|eot_id|><|start_header_id|>assistant<|end_header_id|>\n\n"
        )
        
        response = llm(formatted_prompt, stream=False, max_new_tokens=4096)
        return response
    except Exception as e:
        st.error(f"Error during model generation: {e}")
        return None

# --- Content Parsing (No changes) ---

def fetch_url_content(url):
    """Fetches and parses the main text content from a URL."""
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36'}
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        paragraphs = soup.find_all('p')
        text = ' '.join([p.get_text() for p in paragraphs])
        
        if not text:
            st.warning("Could not extract paragraph text. Falling back to all text.")
            text = soup.get_text(separator=' ', strip=True)
            
        return text
    except Exception as e:
        st.error(f"Error fetching URL: {e}")
        return None

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
            level = indentation // 2
            nodes.append((level, label))
            node_name = f'"{label}"'
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
    dot_string += "  rankdir=LR;\n"
    dot_string += "  " + "\n  ".join(list(dot_nodes)) + "\n"
    dot_string += "  " + "\n  ".join(dot_edges) + "\n"
    dot_string += "}"
    return nodes, dot_string

# --- Session State Initialization ---
def init_session_state():
    defaults = {
        "source_text": None,
        "roadmap_nodes": [],
        "roadmap_dot": None,
        "selected_node_label": None,
        "selected_node_content": None,
        "assignment": None,
        "llm_model": None, # Model object will be stored here
        "model_path": None  # Path to your Llama model
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value