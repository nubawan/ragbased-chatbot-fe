# Z.M.ai

A production-ready RAG-based academic policy chatbot built with Streamlit and Groq.

## Features

- **Document-Based Answers**: Queries PDF documents and scraped web content for accurate responses
- **Modern UI**: Glassmorphism design with animated gradients
- **Anti-Hallucination**: Strict context-based responses with source citations
- **Dynamic Configuration**: All settings configurable via environment variables
- **Free LLM**: Uses Groq's free tier with LLaMA 3.1
- **Local Embeddings**: Uses sentence-transformers (no API key needed)

## Quick Start

### Installation

```bash
# Install dependencies
pip install -r requirements.txt
```

### Configuration

Create a `.streamlit/secrets.toml` file:

```toml
GROQ_API_KEY = "your_groq_api_key_here"
```

Get your free API key from [console.groq.com](https://console.groq.com/keys).

### Run Locally

```bash
streamlit run app.py
```

## Architecture

```
Z.M.AI/
├── app.py                 # Main entry point
├── config/                # Configuration management
│   └── settings.py        # Dynamic settings with env var support
├── core/                  # RAG pipeline components
│   ├── document_loader.py # PDF + web scraping
│   ├── text_processor.py  # Text chunking
│   ├── embeddings.py      # Vector embeddings (sentence-transformers)
│   ├── retriever.py       # Context retrieval
│   └── llm_handler.py     # Groq API integration
├── ui/                    # Streamlit UI
│   ├── styles.py          # CSS styling
│   ├── components.py      # UI components
│   └── chat_interface.py  # Main chat interface
├── utils/                 # Utilities
│   ├── logger.py          # Logging
│   └── validators.py      # Input validation
├── data/                  # Data directory (gitignored)
└── reference/             # Old reference files
```

## RAG Pipeline

1. **Document Loading**: PDF files + web scraping
2. **Text Processing**: Configurable chunking (1000 chars, 200 overlap)
3. **Embeddings**: Local sentence-transformers (all-MiniLM-L6-v2)
4. **Retrieval**: FAISS vector store with cosine similarity
5. **Generation**: Groq API with LLaMA 3.1 8B

## Configuration

All settings are configurable via environment variables:

| Variable | Default | Description |
|----------|---------|-------------|
| `GROQ_API_KEY` | Required | Groq API key |
| `MODEL_NAME` | llama-3.1-8b-instant | LLM model |
| `CHUNK_SIZE` | 1000 | Text chunk size |
| `CHUNK_OVERLAP` | 200 | Chunk overlap |
| `TOP_K_RESULTS` | 5 | Number of results to retrieve |
| `SIMILARITY_THRESHOLD` | 0.7 | Minimum similarity score |
| `SCRAPE_URL` | https://iqra.edu.pk/iu-policies/ | URL to scrape |
| `SCRAPE_ENABLED` | true | Enable web scraping |
| `APP_TITLE` | Z.M.ai | Application title |
| `MAX_HISTORY` | 50 | Max conversation history |
| `THEME_COLOR` | #8b5cf6 | UI theme color |

## Deployment

### Streamlit Cloud

1. Push code to GitHub
2. Connect repository to [Streamlit Cloud](https://streamlit.io/cloud)
3. Add `GROQ_API_KEY` in secrets
4. Deploy!

No additional hosting needed - Streamlit Cloud handles everything.

## Data Sources

- **PDF**: Academic Policy Manual for Students
- **Web**: iqra.edu.pk/iu-policies/

## Tech Stack

- **Framework**: Streamlit
- **LLM**: Groq (LLaMA 3.1 8B)
- **Embeddings**: sentence-transformers (local)
- **Vector Store**: FAISS
- **PDF Processing**: pypdf, pdfplumber
- **Web Scraping**: trafilatura, BeautifulSoup

## License

MIT
