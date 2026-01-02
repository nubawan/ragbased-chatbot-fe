import os
import streamlit as st
import requests
import datetime

# -------------------- 1. BRANDING & CONFIG --------------------
st.set_page_config(page_title="MiRAG | Chat", layout="centered", page_icon="💬")

# Fetch API Key
if "GROQ_API_KEY" in st.secrets:
    GROQ_API_KEY = st.secrets["GROQ_API_KEY"]
else:
    GROQ_API_KEY = os.getenv("GROQ_API_KEY")

# --- PROPER PATH LOGIC ---
# This defines the base directory where your script is located
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_NAME = "llama-3.1-8b-instant"

# -------------------- 2. SIDEBAR (PROJECT DETAILS) --------------------
with st.sidebar:
    st.title("🤖 MiRAG Bot")
    st.markdown("---")
    st.markdown("### **Project Info**")
    st.write(f"**Location:** `{BASE_DIR}`") # Shows the system path
    st.write("**Status:** ✅ Online")
    
    st.markdown("---")
    st.markdown("### **Developed By:**")
    st.info("👤 Mir MUHAMMAD Rafique\n\n👤 Hasnain Ali Raza")
    
    if st.button("🗑️ Clear Conversation"):
        st.session_state.messages = []
        st.rerun()

# -------------------- 3. CHAT LOGIC --------------------
def mirag_chat(question, history):
    today = datetime.datetime.now().strftime("%d %B %Y")
    
    # The system prompt defines the bot's personality
    system_prompt = f"""
    You are MiRAG, a helpful AI assistant.
    Created by: Mir MUHAMMAD Rafique and Hasnain Ali Raza.
    Current Date: {today}.
    Instructions: Be polite, conversational, and assist the user with any topic.
    """

    messages = [{"role": "system", "content": system_prompt}] + history + [{"role": "user", "content": question}]

    try:
        response = requests.post(
            "https://api.groq.com/openai/v1/chat/completions", 
            json={"model": MODEL_NAME, "messages": messages, "temperature": 0.7},
            headers={"Authorization": f"Bearer {GROQ_API_KEY}"}
        )
        return response.json()["choices"][0]["message"]["content"]
    except Exception as e:
        return f"⚠️ Connection Error: Please ensure your API Key is set correctly."

# -------------------- 4. MAIN USER INTERFACE --------------------
st.title("💬 MiRAG Chat")
st.subheader("Official Chat Interface")

# Initialize Session State
if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "assistant", "content": "Assalam o Alaikum! I am MiRAG. How can I help you and Hasnain today?"}]

# Display Conversation History
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# User Input
if user_input := st.chat_input("Type your message here..."):
    # Save user message
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)
    
    # Get AI Response
    with st.chat_message("assistant"):
        with st.spinner("MiRAG is typing..."):
            ans = mirag_chat(user_input, st.session_state.messages[:-1])
            st.markdown(ans)
    
    # Save assistant message
    st.session_state.messages.append({"role": "assistant", "content": ans})
