import os
import streamlit as st
import pdfplumber
import requests
import datetime

# -------------------- 1. BRANDING & CONFIG --------------------
st.set_page_config(page_title="MiRAG | Academic Assistant", layout="centered", page_icon="🎓")

# API Key Handling (Fetch from Streamlit Secrets)
if "GROQ_API_KEY" in st.secrets:
    GROQ_API_KEY = st.secrets["GROQ_API_KEY"]
else:
    GROQ_API_KEY = os.getenv("GROQ_API_KEY")

# --- THE PROPER PATH ---
# This looks for the file in the same GitHub folder as this script
PDF_FILENAME = "Academic-Policy-Manual-for-Students2.pdf"
MODEL_NAME = "llama-3.1-8b-instant"

# -------------------- 2. AUTOMATIC PDF INDEXING --------------------
@st.cache_data(show_spinner="MiRAG is connecting to the Policy Manual...")
def load_and_index_manual():
    # Verify if the file exists in the container
    if not os.path.exists(PDF_FILENAME):
        return None
    
    text = ""
    try:
        with pdfplumber.open(PDF_FILENAME) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
        
        # Divide manual into searchable segments (chunks)
        lines = [line.strip() for line in text.split("\n") if line.strip()]
        chunks, current_chunk = [], ""
        for line in lines:
            if len(current_chunk) + len(line) < 700:
                current_chunk += " " + line
            else:
                chunks.append(current_chunk.strip())
                current_chunk = line
        if current_chunk:
            chunks.append(current_chunk.strip())
        return chunks
    except Exception:
        return None

# Load chunks immediately
policy_chunks = load_and_index_manual()

# -------------------- 3. RETRIEVAL & CHAT LOGIC --------------------
def get_context(query):
    if not policy_chunks:
        return ""
    
    query_words = set(query.lower().split())
    matches = []
    for chunk in policy_chunks:
        score = len(query_words & set(chunk.lower().split()))
        if score > 0:
            matches.append((score, chunk))
    
    matches.sort(key=lambda x: x[0], reverse=True)
    return "\n\n".join([item[1] for item in matches[:3]])

def ask_mirag(question, history):
    context = get_context(question)
    today = datetime.datetime.now().strftime("%d %B %Y")
    
    # Identity Prompt for the group
    system_prompt = f"""
    You are MiRAG, an Academic Assistant.
    Created by: Mir MUHAMMAD Rafique and Hasnain Ali Raza.
    Current Date: {today}.
    
    Use this Context from the Policy Manual:
    {context}
    
    Instructions: Provide precise details from the manual. 
    If information is missing, inform the user clearly.
    """

    messages = [{"role": "system", "content": system_prompt}] + history + [{"role": "user", "content": question}]

    try:
        response = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            json={"model": MODEL_NAME, "messages": messages, "temperature": 0.2},
            headers={"Authorization": f"Bearer {GROQ_API_KEY}"}
        )
        return response.json()["choices"][0]["message"]["content"]
    except:
        return "⚠️ Connection Error. Check the API Key in Secrets."

# -------------------- 4. USER INTERFACE --------------------
st.title("🤖 MiRAG: Academic AI")
st.subheader("Developed by Mir MUHAMMAD Rafique & Hasnain Ali Raza")

with st.sidebar:
    st.header("Connection Status")
    if policy_chunks:
        st.success(f"✅ Linked to {PDF_FILENAME}")
    else:
        st.error("❌ PDF Missing")
        st.write(f"Ensure '{PDF_FILENAME}' is in the GitHub root folder.")

if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "assistant", "content": "Assalam o Alaikum! I am MiRAG. I am connected to the Academic Policy Manual. Ask me anything!"}]

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

if prompt := st.chat_input("Ask about admissions, grading, or attendance..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("Analyzing Policy Manual..."):
            answer = ask_mirag(prompt, st.session_state.messages[:-1])
            st.markdown(answer)
        st.session_state.messages.append({"role": "assistant", "content": answer})
