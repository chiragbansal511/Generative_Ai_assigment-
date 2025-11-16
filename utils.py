import streamlit as st
import google.generativeai as genai
import time
import re
import io
import pypdf

# --- Gemini API Configuration ---
def configure_gemini(api_key):
    """Configures the Generative AI model with the provided API key and safety settings."""
    try:
        genai.configure(api_key=api_key)
        generation_config = {
            "temperature": 0.7,
            "top_p": 1,
            "top_k": 1,
            "max_output_tokens": 4096,
        }
        safety_settings = [
            {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
            {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
            {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
            {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
        ]
        model = genai.GenerativeModel(
            model_name="gemini-2.5-flash-preview-09-2025",
            generation_config=generation_config,
            safety_settings=safety_settings
        )
        return model
    except Exception as e:
        st.error(f"Error configuring Gemini: {e}")
        return None

def call_gemini_api(model, prompt, max_retries=5):
    """Calls the Gemini API (synchronously) with exponential backoff."""
    delay = 1
    for i in range(max_retries):
        try:
            response = model.generate_content(prompt)
            return response.text
        except Exception as e:
            if "quota" in str(e).lower() or "rate limit" in str(e).lower():
                st.warning(f"Rate limit exceeded. Retrying in {delay}s... ({i+1}/{max_retries})")
                time.sleep(delay)
                delay *= 2
            else:
                st.error(f"An unexpected error occurred with the Gemini API: {e}")
                return None
    st.error("Failed to get a response from Gemini after several retries. Please check your quota.")
    return None

# --- PDF and Text Parsing ---
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

# --- Roadmap Parsing and DOT String Generation ---
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

# --- Session State Initialization ---
def init_session_state():
    """Initializes session state variables."""
    defaults = {
        "source_text": None,
        "roadmap_nodes": [],
        "roadmap_dot": None,
        "selected_node_label": None,
        "selected_node_content": None,
        "assignment": None,
        "gemini_model": None
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value