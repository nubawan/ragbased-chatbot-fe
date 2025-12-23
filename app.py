import os
import streamlit as st
import pdfplumber
import requests
import datetime

# -------------------- 1. BASIC SETUP --------------------
st.set_page_config(page_title="Z&J ka Chatbot", layout="centered", page_icon="🤖")

# API Configuration from Secrets
if "GROQ_API_KEY" in st.secrets:
    GROQ_API_KEY = st.secrets["GROQ_API_KEY"]
else:
    st.error("⚠️ Error: 'GROQ_API_KEY' not found in Streamlit Secrets!")
    st.stop()

PDF_PATH = "Academic-Policy-Manual-for-Students2.pdf"
MODEL_NAME = "llama-3.1-8b-instant"

# -------------------- 2. LOAD + CHUNK PDF --------------------
@st.cache_data(show_spinner="Z&J's Brain is loading the PDF...")
def load_chunks(max_chars: int = 600):
    if not os.path.exists(PDF_PATH):
        return []  # Return empty if file is missing
    
    text = ""
    try:
        with pdfplumber.open(PDF_PATH) as pdf:
            for page in pdf.pages:
                tx = page.extract_text()
                if tx:
                    text += tx + "\n"
    except Exception as e:
        st.error(f"Error reading PDF: {e}")
        return []

    raw_parts = [p.strip() for p in text.split("\n") if p.strip()]
    chunks = []
    buf = ""

    for part in raw_parts:
        if len(buf) + len(part) <= max_chars:
            buf += " " + part
        else:
            if buf.strip():
                chunks.append(buf.strip())
            buf = part

    if buf.strip():
        chunks.append(buf.strip())
    return chunks

# Initialize chunks
pdf_chunks = load_chunks()

# -------------------- 3. SIMPLE RETRIEVAL --------------------
def retrieve_context(query: str, top_k: int = 3):
    if not pdf_chunks:
        return ""
        
    q_words = set(query.lower().split())
    scored = []

    for ch in pdf_chunks:
        ch_words = set(ch.lower().split())
        # Score based on keyword overlap
        score = len(q_words & ch_words)
        if score > 0:
            scored.append((score, ch))

    if not scored:
        return ""

    # Sort by highest score and take top K
    scored.sort(reverse=True, key=lambda x: x[0])
    return "\n\n".join([c for _, c in scored[:top_k]])

# -------------------- 4. GROQ API CALL --------------------
def llama_chat(messages):
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": MODEL_NAME,
        "messages": messages,
        "temperature": 0.4,
    }

    try:
        response = requests.post(url, json=payload, headers=headers, timeout=15)
        response.raise_for_status() # Raise error for bad status codes
        result = response.json()
        return result["choices"][0]["message"]["content"]
    except requests.exceptions.Timeout:
        return "⚠️ Error: The request timed out. Please try again."
    except Exception as e:
        return f"⚠️ Groq API Error: {str(e)}"

# -------------------- 5. RAG LOGIC --------------------
def get_answer(question: str, history):
    context = retrieve_context(question)
    today = datetime.datetime.now().strftime("%d %B %Y")
    
    # Prompt Engineering
    if not context.strip():
        system_prompt = f"You are Z&J ka Chatbot. Rules: Direct answers, use updated general knowledge (Today: {today}). Do NOT say 'searching' or 'checking'. Never limit info to 2023."
    else:
        system_prompt = f"""
You are Z&J ka Chatbot. Use the following PDF context. If needed, blend in general knowledge (Today: {today}).
Rules: Confident answers. Do NOT say 'I am searching'. Never limit info to 2023.

PDF Context:
{context}
"""

    # Prepare message list (Memory)
    messages = [{"role": "system", "content": system_prompt}]
    for m in history[-6:]: # Memory of last 6 exchanges
        messages.append(m)
    messages.append({"role": "user", "content": question})

    return llama_chat(messages)

# -------------------- 6. STREAMLIT UI --------------------
st.title("🤖 Z&J ka Chatbot")

# Clear History Button
if st.sidebar.button("Clear Chat"):
    st.session_state.messages = []
    st.rerun()

if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant",
         "content": "Assalam o Alaikum! 👋 Main Z&J ka Chatbot hoon. Jo Bhi Phouchna Bindaas Phoucho Mai Ho Na Apki Madad Kay Liye"}
    ]

# Display history
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# User input
if user_input := st.chat_input("Apna sawal likho..."):
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)

    with st.chat_message("assistant"):
        with st.spinner("Soch raha hoon..."):
            answer = get_answer(user_input, st.session_state.messages[:-1])
        st.markdown(answer)
        st.session_state.messages.append({"role": "assistant", "content": answer})
