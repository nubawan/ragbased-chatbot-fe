import os
import streamlit as st
from langchain_community.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from groq import Groq
from dotenv import load_dotenv

# === 1. MiRAG Configuration & Paths ===
st.set_page_config(page_title="MiRAG | Personal Assistant", page_icon="🤖", layout="wide")
load_dotenv()
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

# Define permanent paths for persistence
DATA_PATH = "mirag_data"      # Directory for uploaded PDFs
DB_PATH = "mirag_vector_db"   # Directory for the FAISS index
os.makedirs(DATA_PATH, exist_ok=True)

st.markdown("<h2 style='text-align: center;'>🤖 MiRAG: My Intelligent RAG</h2>", unsafe_allow_html=True)
st.divider()

# === 2. Document Processing with Persistence Path ===
@st.cache_resource(show_spinner="🧠 Initializing MiRAG Brain...")
def prepare_vectorstore(uploaded_file):
    # Create a unique path for the uploaded document
    file_path = os.path.join(DATA_PATH, uploaded_file.name)
    
    with open(file_path, "wb") as f:
        f.write(uploaded_file.getbuffer())
    
    # Load and Split
    loader = PyPDFLoader(file_path)
    pages = loader.load()
    splitter = RecursiveCharacterTextSplitter(chunk_size=600, chunk_overlap=100)
    chunks = splitter.split_documents(pages)
    
    # Embeddings Path Logic
    embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
    
    # Check if a persistent path exists to avoid re-embedding
    if os.path.exists(DB_PATH):
        vectorstore = FAISS.load_local(DB_PATH, embeddings, allow_dangerous_deserialization=True)
        # Merge new data if it's a new file
        new_db = FAISS.from_documents(chunks, embeddings)
        vectorstore.merge_from(new_db)
    else:
        vectorstore = FAISS.from_documents(chunks, embeddings)
    
    # Save the updated "brain" to the persistent path
    vectorstore.save_local(DB_PATH)
    return vectorstore

# Sidebar for Dynamic Uploads
with st.sidebar:
    st.header("📁 Personal Data")
    uploaded_file = st.file_uploader("Upload a PDF to MiRAG", type="pdf")
    
    if st.button("Clear History & DB"):
        st.session_state.messages = []
        # Clear the physical paths
        if os.path.exists(DB_PATH):
            import shutil
            shutil.rmtree(DB_PATH)
        st.rerun()

# === 3. Chat Logic ===
if uploaded_file:
    vectorstore = prepare_vectorstore(uploaded_file)
    
    if "messages" not in st.session_state:
        st.session_state.messages = []

    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    if query := st.chat_input("Ask MiRAG something..."):
        st.session_state.messages.append({"role": "user", "content": query})
        with st.chat_message("user"):
            st.markdown(query)

        # Retrieval & Generation
        retriever = vectorstore.as_retriever(search_kwargs={"k": 4})
        docs = retriever.invoke(query)  # Modern LangChain 'invoke' path
        context = "\n\n".join([doc.page_content for doc in docs])
        
        client = Groq(api_key=GROQ_API_KEY)
        response = client.chat.completions.create(
            model="llama3-70b-8192",
            messages=[
                {"role": "system", "content": "You are MiRAG, a precise assistant. Use the context to answer."},
                {"role": "user", "content": f"Context: {context}\n\nQuestion: {query}"}
            ],
            temperature=0.2
        )
        
        answer = response.choices[0].message.content
        with st.chat_message("assistant"):
            st.markdown(answer)
        st.session_state.messages.append({"role": "assistant", "content": answer})
else:
    st.info("👋 Welcome! Upload a PDF (like the Iqra Academic Policy) to begin.")
