import streamlit as st
import io
import pypdf
import requests
import re
from bs4 import BeautifulSoup
import google.generativeai as genai

# --- Gemini Configuration ---
def configure_gemini(api_key):
    """Configures the Gemini model with the provided API key."""
    try:
        genai.configure(api_key=api_key)
        
        # UPDATED: Using the latest stable model for late 2025
        model_name = 'gemini-2.5-flash' 
        
        model = genai.GenerativeModel(model_name)
        return model
    except Exception as e:
        st.error(f"Error configuring Gemini: {e}")
        return None

def call_gemini_api(model, prompt):
    """Calls the Gemini API to generate content."""
    if not model:
        st.error("Gemini model is not configured.")
        return None
    
    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        # Helper to debug model names if 2.5 fails
        if "404" in str(e) or "not found" in str(e).lower():
            st.error(f"Model Error: {e}")
            st.warning("Attempting to list available models for your API key...")
            try:
                available = [m.name for m in genai.list_models()]
                st.code(f"Available Models:\n{available}")
            except:
                st.error("Could not list models.")
        else:
            st.error(f"Error calling Gemini API: {e}")
        return None

# --- Content Parsing ---

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

# --- Roadmap Parsing ---
def parse_roadmap_to_dot(markdown_text):
    """Parses the markdown list into a Graphviz DOT format."""
    if not markdown_text:
        return [], ""
    nodes = []
    dot_edges = []
    dot_nodes = set()
    parent_stack = []
    
    lines = markdown_text.split('\n')
    
    for line in lines:
        match = re.match(r'^(\s*)[-*]\s(.*)', line)
        if match:
            indentation = len(match.group(1))
            label = match.group(2).strip()
            level = indentation // 2
            
            nodes.append((level, label))
            
            safe_label = label.replace('"', "'")
            node_name = f'"{safe_label}"'
            
            while len(parent_stack) > level:
                parent_stack.pop()
                
            if parent_stack:
                parent_label = parent_stack[-1].replace('"', "'")
                parent_name = f'"{parent_label}"'
                dot_edges.append(f'{parent_name} -> {node_name};')
            else:
                dot_nodes.add(f'{node_name};')
            
            parent_stack.append(label)
            
    dot_string = "digraph G {\n"
    dot_string += "  node [shape=box, style=rounded, fontname=Helvetica, fillcolor=\"#E6F7FF\", style=filled];\n"
    dot_string += "  edge [fontname=Helvetica];\n"
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
        "gemini_api_key": None,
        "gemini_model": None
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value