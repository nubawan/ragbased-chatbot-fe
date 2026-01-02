import os
import streamlit as st
import pdfplumber
import requests
import datetime

# -------------------- 1. IDENTITY & CONFIG --------------------
st.set_page_config(page_title="MiRAG | Academic Assistant", layout="centered", page_icon="🎓")

# API Key Handling (Fetch from Streamlit Secrets)
if "GROQ_API_KEY" in st.secrets:
    GROQ_API_KEY = st.secrets["GROQ_API_KEY"]
else:
    GROQ_API_KEY = os.getenv("GROQ_API_KEY")

# --- FILE PATH ---
# Connects to the manual uploaded on GitHub
PDF_FILENAME = "Academic-Policy-Manual-for-Students2.pdf"
MODEL_NAME = "llama-3.1-8b-instant"

# -------------------- 2. AUTOMATIC PDF INDEXING --------------------
@st.cache_data(show_spinner="MiRAG is indexing the Policy Manual...")
def load_and_index_manual():
    # Verify if the file exists in the GitHub root folder
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

# Load policy data immediately
policy_chunks = load_and_index_manual()

# -------------------- 3. RETRIEVAL & CHAT LOGIC --------------------
def get_context(query):
    if not policy_chunks:
        return ""
    
    # Keyword search to find relevant policy sections
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
    
    # SYSTEM PROMPT: Set identity as MiRAG and credit the developers
    system_prompt = f"""
    You are MiRAG, a professional Academic AI Assistant.
    Developed by: Mir MUHAMMAD and Hasnain Ali Raza.
    Current Date: {today}.
    
    Instructions:
    - Use the provided PDF context to answer questions about university policy.
    - If the context contains specific numbers (GPA, %, attendance hours), include them.
    - If the context does not contain the answer, use your general knowledge but clarify it is general info.
    - Do NOT mention "searching" or "researching." Provide direct answers.

    ACADEMIC POLICY CONTEXT:
    {context}
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
        return "⚠️ Connection Error. Mir & Hasnain, please check the Groq API Key settings!"

# -------------------- 4. USER INTERFACE (UI) --------------------
st.title("🤖 MiRAG: Academic AI")
st.subheader("Developed by Mir MUHAMMAD & Hasnain Ali Raza")

with st.sidebar:
    st.header("System Status")
    if policy_chunks:
        st.success(f"✅ Linked to {PDF_FILENAME}")
        st.info(f"Loaded {len(policy_chunks)} policy segments.")
    else:
        st.error("❌ PDF Manual Not Found")
        st.write("Ensure the PDF is in the root directory on GitHub.")

if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "assistant", "content": "Hello! I am MiRAG. I have been programmed by Mir MUHAMMAD and Hasnain Ali Raza to assist you with academic policies. How can I help you today?"}]

# Display Chat History
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# User Input
if prompt := st.chat_input("Ask about admissions, grading, or attendance..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("MiRAG is analyzing the manual..."):
            answer = ask_mirag(prompt, st.session_state.messages[:-1])
            st.markdown(answer)
        st.session_state.messages.append({"role": "assistant", "content": answer})
