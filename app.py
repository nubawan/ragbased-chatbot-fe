import os
import streamlit as st
import pdfplumber
import requests
import datetime

# -------------------- 1. BASIC SETUP --------------------
st.set_page_config(
    page_title="MiRAG - Mir MUHAMMAD Rafique's Chat Bot",
    layout="centered",
    page_icon="🤖"
)

# API Configuration from Secrets (Recommended for Streamlit Cloud)
if "GROQ_API_KEY" in st.secrets:
    GROQ_API_KEY = st.secrets["GROQ_API_KEY"]
else:
    st.error("⚠️ Error: 'GROQ_API_KEY' not found in Streamlit Secrets! Please add it in Settings > Secrets.")
    st.stop()

PDF_PATH = "Academic-Policy-Manual-for-Students2.pdf"
MODEL_NAME = "llama-3.1-8b-instant"  # Fast and capable model

# -------------------- 2. LOAD + CHUNK PDF --------------------
@st.cache_data(show_spinner="🧠 Loading MiRAG's knowledge from PDF...")
def load_chunks(max_chars: int = 600):
    if not os.path.exists(PDF_PATH):
        st.warning(f"PDF file '{PDF_PATH}' not found. General mode only.")
        return []
   
    text = ""
    try:
        with pdfplumber.open(PDF_PATH) as pdf:
            for page in pdf.pages:
                tx = page.extract_text()
                if tx:
                    text += tx + "\n"
        st.success(f"✅ Successfully loaded {len(pdf.pages)} pages from the Academic Policy Manual.")
    except Exception as e:
        st.error(f"Error reading PDF: {e}")
        return []
    
    # Simple chunking by approximate character limit
    raw_parts = [p.strip() for p in text.split("\n") if p.strip()]
    chunks = []
    buf = ""
    for part in raw_parts:
        if len(buf) + len(part) + 1 <= max_chars:
            buf += " " + part
        else:
            if buf.strip():
                chunks.append(buf.strip())
            buf = part
    if buf.strip():
        chunks.append(buf.strip())
    
    st.info(f"📚 Created {len(chunks)} knowledge chunks for fast retrieval.")
    return chunks

# Initialize chunks once
pdf_chunks = load_chunks()

# -------------------- 3. SIMPLE RETRIEVAL (Keyword Overlap) --------------------
def retrieve_context(query: str, top_k: int = 4):
    if not pdf_chunks:
        return ""
       
    q_words = set(query.lower().split())
    scored = []
    for ch in pdf_chunks:
        ch_words = set(ch.lower().split())
        score = len(q_words & ch_words)
        if score > 0:
            scored.append((score, ch))
    
    if not scored:
        return ""
    
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
        "max_tokens": 1024,
    }
    try:
        response = requests.post(url, json=payload, headers=headers, timeout=20)
        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"]
    except requests.exceptions.Timeout:
        return "⚠️ Request timed out. Please try again in a moment."
    except requests.exceptions.HTTPError as http_err:
        return f"⚠️ API Error: {http_err}"
    except Exception as e:
        return f"⚠️ Unexpected error: {str(e)}"

# -------------------- 5. RAG LOGIC --------------------
def get_answer(question: str, history):
    context = retrieve_context(question)
    today = datetime.datetime.now().strftime("%d %B %Y")

    if context.strip():
        system_prompt = f"""
You are MiRAG - Mir MUHAMMAD Rafique's personal intelligent chatbot.
You have access to the Iqra University Academic Policy Manual. Use the provided context to answer accurately.
If the question is outside the document, use your general knowledge confidently.
Today's date: {today}

PDF Context:
{context}
"""
    else:
        system_prompt = f"""
You are MiRAG - Mir MUHAMMAD Rafique's personal intelligent chatbot.
Answer questions confidently and helpfully using up-to-date knowledge.
Today's date: {today}
Be friendly, clear, and professional.
"""

    messages = [{"role": "system", "content": system_prompt}]
    # Keep last 6 exchanges for context (short-term memory)
    for m in history[-6:]:
        messages.append(m)
    messages.append({"role": "user", "content": question})

    return llama_chat(messages)

# -------------------- 6. STREAMLIT UI --------------------
st.markdown("""
<h1 style='text-align: center;'>🤖 MiRAG</h1>
<h3 style='text-align: center; color: #666;'>Mir MUHAMMAD Rafique's Chat Bot</h3>
""", unsafe_allow_html=True)

st.sidebar.header("🛠 Controls")
if st.sidebar.button("🗑️ Clear Chat History"):
    st.session_state.messages = []
    st.rerun()

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant",
         "content": "Assalam o Alaikum! 👋\n\nI am **MiRAG**, Mir MUHAMMAD Rafique's personal AI chatbot.\n\n"
                    "I can answer questions about the **Iqra University Academic Policy** or anything else using the latest knowledge.\n\n"
                    "How can I assist you today?"}
    ]

# Display chat messages
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# User input
if user_input := st.chat_input("Ask me anything..."):
    # Add user message
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)

    # Generate and display assistant response
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            answer = get_answer(user_input, st.session_state.messages[:-1])
        st.markdown(answer)
        st.session_state.messages.append({"role": "assistant", "content": answer})
