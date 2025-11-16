import streamlit as st
import time
import re
import io
import pypdf
import os
import requests
from bs4 import BeautifulSoup
from ctransformers import AutoModelForCausalLM

# --- Model Constants ---
# THIS IS THE FIX: We are pointing to a different, more stable model file.
MODEL_URL = "https://huggingface.co/microsoft/Phi-3-mini-4k-instruct-gguf/blob/main/Phi-3-mini-4k-instruct-q5_k_m.gguf?download=true"
MODEL_FILENAME = "Phi-3-mini-4k-instruct-q5_k_m.gguf"

# --- Model Loading & Auto-Downloading ---

def download_model_with_progress(url, filename):
    """Downloads a file from a URL and displays a Streamlit progress bar."""
    try:
        with requests.get(url, stream=True) as r:
            r.raise_for_status()
            total_size_in_bytes = int(r.headers.get('content-length', 0))
            bytes_downloaded = 0
            
            st.info(f"Downloading new model: {filename} (~2.6 GB)") # Updated size
            progress_bar = st.progress(0, text="Starting download...")
            
            with open(filename, 'wb') as f:
                for chunk in r.iter_content(chunk_size=8192):
                    bytes_downloaded += len(chunk)
                    f.write(chunk)
                    
                    if total_size_in_bytes > 0:
                        progress = min(int((bytes_downloaded / total_size_in_bytes) * 100), 100)
                        progress_bar.progress(progress, text=f"Downloading... {progress}%")
                    
            progress_bar.progress(100, text="Download complete!")
            st.success("Model downloaded successfully!")
            time.sleep(2) # Give user time to see message
            progress_bar.empty()
            
    except Exception as e:
        st.error(f"Error downloading model: {e}")
        st.error("Please ensure you have a stable internet connection and try again.")
        if os.path.exists(filename):
            os.remove(filename) # Remove partial download
        return False
    return True

def get_model_path():
    """
    Checks if the model file exists. If not, triggers the download.
    Returns the path to the model file.
    """
    if not os.path.exists(MODEL_FILENAME):
        if not download_model_with_progress(MODEL_URL, MODEL_FILENAME):
            return None # Download failed
    return MODEL_FILENAME

@st.cache_resource
def load_model(model_path):
    """Loads the GGUF model from the given file path."""
    if not model_path:
        return None
    try:
        # We are correctly specifying the model_type: "phi3"
        llm = AutoModelForCausalLM.from_pretrained(model_path, model_type="phi3")
        return llm
    except Exception as e:
        st.error(f"Error loading model: {e}")
        return None

def call_model_api(llm, prompt):
    """Calls the loaded CTransformer model with the Phi-3 chat template."""
    if not llm:
        st.error("Model is not loaded.")
        return None
    
    try:
        formatted_prompt = f"<|user|>\n{prompt}<|end|>\n<|assistant|>"
        response = llm(formatted_prompt, stream=False, max_new_tokens=4096)
        return response
    except Exception as e:
        st.error(f"Error during model generation: {e}")
        return None

# --- Content Parsing (No changes) ---

def fetch_url_content(url):
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

# --- Session State Initialization (No changes) ---
def init_session_state():
    defaults = {
        "source_text": None,
        "roadmap_nodes": [],
        "roadmap_dot": None,
        "selected_node_label": None,
        "selected_node_content": None,
        "assignment": None,
        "llm_model": None 
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value