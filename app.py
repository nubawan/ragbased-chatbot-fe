import os
import streamlit as st
import pdfplumber
import requests
import datetime

# -------------------- 1. BRANDING & CONFIG --------------------
st.set_page_config(page_title="MiRAG | Academic Assistant", layout="centered", page_icon="🤖")

# Securely fetch API Key
if "GROQ_API_KEY" in st.secrets:
    GROQ_API_KEY = st.secrets["GROQ_API_KEY"]
else:
    GROQ_API_KEY = os.getenv("GROQ_API_KEY")
    if not GROQ_API_KEY:
        st.error("⚠️ GROQ_API_KEY missing! Please add it to Streamlit Secrets.")
        st.stop()

PDF_PATH = "Academic-Policy-Manual-for-Students2.pdf" 
MODEL_NAME = "llama-3.1-8b-instant"

# -------------------- 2. AUTO-LOAD POLICY --------------------
@st.cache_data(show_spinner="MiRAG is syncing with the Policy Manual...")
def load_mirag_brain(path: str):
    if not os.path.exists(path):
        st.warning(f"⚠️ {path} not found.")
        return []
    
    text = ""
    try:
        with pdfplumber.open(path) as pdf:
            for page in pdf.pages:
                tx = page.extract_text()
                if tx: text += tx + "\n"
    except Exception as e:
        st.error(f"Error reading PDF: {e}")
        return []

    lines = [l.strip() for l in text.split("\n") if l.strip()]
    chunks, buf = [], ""
    for line in lines:
        if len(buf) + len(line) <= 600:
            buf += " " + line
        else:
            chunks.append(buf.strip())
            buf = line
    if buf: chunks.append(buf.strip())
    return chunks

policy_data = load_mirag_brain(PDF_PATH)

# -------------------- 3. SMART RETRIEVAL --------------------
def get_context(query: str):
    if not policy_data: return ""
    q_words = set(query.lower().split())
    scored = []
    for c in policy_data:
        score = len(q_words & set(c.lower().split()))
        if score > 0: scored.append((score, c))
    scored.sort(key=lambda x: x[0], reverse=True)
    return "\n\n".join([c for score, c in scored[:3]])

# -------------------- 4. MiRAG INTELLIGENCE --------------------
def mirag_chat(question: str, history):
    context = get_context(question)
    today = datetime.datetime.now().strftime("%d %B %Y")
    
    # System prompt updated to include both partners
    system_prompt = f"""
You are MiRAG (Mir MUHAMMAD Rafique and Hasnain Ali Raza's Chat Bot), a professional Academic Policy Assistant.
Current Date: {today}.

CORE INSTRUCTIONS:
1. Primary Source: Use the PDF context provided.
2. 2025 Updates: 
   - Passing threshold: 50% for undergraduates. 
   - "XF" grade: Failure due to attendance shortage. 
   - Probation limit: 1.70 Semester GPA.
3. Style: Professional and direct. 
4. DO NOT mention "checking the database".

PDF Context:
{context}
"""

    messages = [{"role": "system", "content": system_prompt}]
    for m in history:
        messages.append({"role": m["role"], "content": m["content"]})
    messages.append({"role": "user", "content": question})

    try:
        payload = {"model": MODEL_NAME, "messages": messages, "temperature": 0.3}
        headers = {"Authorization": f"Bearer {GROQ_API_KEY}"}
        r = requests.post("https://api.groq.com/openai/v1/chat/completions", json=payload, headers=headers)
        r.raise_for_status()
        return r.json()["choices"][0]["message"]["content"]
    except Exception as e:
        return f"⚠️ MiRAG Connection Error: {str(e)}"

# -------------------- 5. USER INTERFACE --------------------

# --- SIDEBAR BRANDING ---
with st.sidebar:
    st.title("🤖 MiRAG Info")
    st.markdown("---")
    st.markdown("### **Developers:**")
    st.write("👤 **Mir MUHAMMAD Rafique**")
    st.write("👤 **Hasnain Ali Raza**")
    st.markdown("---")
    st.info("This ChatBot is designed to assist students with Academic Policy queries.")
    if st.button("Clear Chat History"):
        st.session_state.messages = [{"role": "assistant", "content": "Assalam o Alaikum! History cleared. How can I help you?"}]
        st.rerun()

# --- MAIN INTERFACE ---
st.title("🤖 MiRAG")
st.subheader("Mir MUHAMMAD Rafique & Hasnain Ali Raza's ChatBot")

if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "assistant", "content": "Assalam o Alaikum! I am MiRAG. I have indexed your Academic Policy. How can I assist you?"}]

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

if user_input := st.chat_input("Ask MiRAG about university policies..."):
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)

    with st.chat_message("assistant"):
        with st.spinner("MiRAG is analyzing..."):
            ans = mirag_chat(user_input, st.session_state.messages[:-1])
            st.markdown(ans)
    
    st.session_state.messages.append({"role": "assistant", "content": ans})
