"""
Z.M.ai - Chat Interface Module

Main chat interface that handles user interactions.
"""

import logging
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, field

import streamlit as st

from config import get_ui_config, get_groq_config
from core import RAGPipeline, RAGLLMHandler, DocumentLoader
from . import (
    inject_custom_css,
    render_header,
    render_welcome_message,
    render_message,
    render_sidebar,
    render_footer,
    render_loading_state,
    render_error_state,
)

logger = logging.getLogger(__name__)


@dataclass
class ChatMessage:
    """Represents a single chat message."""
    role: str  # "user", "assistant", "error"
    content: str
    sources: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "role": self.role,
            "content": self.content,
            "sources": self.sources,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ChatMessage":
        """Create from dictionary."""
        return cls(
            role=data.get("role", "assistant"),
            content=data.get("content", ""),
            sources=data.get("sources", []),
        )


class ChatInterface:
    """
    Main chat interface for Z.M.ai.

    Manages the complete chat experience including:
    - Message history
    - RAG pipeline
    - LLM responses
    - UI rendering
    """

    def __init__(self):
        """Initialize the chat interface."""
        self.ui_config = get_ui_config()
        self.groq_config = get_groq_config()

        # Initialize RAG components
        self.document_loader = DocumentLoader()
        self.rag_pipeline = RAGPipeline()
        self.llm_handler = RAGLLMHandler()

        # Check API key
        self.api_key_configured = bool(self.groq_config.api_key)

        # Initialize session state
        self._init_session_state()

    def _init_session_state(self):
        """Initialize Streamlit session state variables."""
        if "messages" not in st.session_state:
            st.session_state.messages = []

        if "pipeline_initialized" not in st.session_state:
            st.session_state.pipeline_initialized = False

        if "initialization_error" not in st.session_state:
            st.session_state.initialization_error = None

    def initialize_pipeline(self) -> bool:
        """
        Initialize the RAG pipeline with documents.

        Returns:
            True if successful, False otherwise
        """
        if st.session_state.pipeline_initialized:
            return True

        try:
            with st.spinner("Loading knowledge base..."):
                # Load all sources
                documents = self.document_loader.load_all_sources()

                if not documents:
                    st.session_state.initialization_error = (
                        "No documents could be loaded. Please check that the PDF file exists "
                        "and the website is accessible."
                    )
                    return False

                # Initialize pipeline
                success = self.rag_pipeline.initialize(documents)

                if success:
                    st.session_state.pipeline_initialized = True
                    logger.info("RAG pipeline initialized successfully")
                    return True
                else:
                    st.session_state.initialization_error = (
                        "Failed to initialize the knowledge base. Please try again."
                    )
                    return False

        except Exception as e:
            logger.error(f"Pipeline initialization error: {e}")
            st.session_state.initialization_error = f"Initialization failed: {str(e)}"
            return False

    def clear_chat(self):
        """Clear the chat history."""
        st.session_state.messages = []
        logger.info("Chat cleared")

    def add_message(self, role: str, content: str, sources: Optional[List[str]] = None):
        """
        Add a message to the chat history.

        Args:
            role: Message role ("user", "assistant", "error")
            content: Message content
            sources: Optional source citations
        """
        st.session_state.messages.append(ChatMessage(
            role=role,
            content=content,
            sources=sources or [],
        ))

        # Limit history size
        max_history = self.ui_config.max_history
        if len(st.session_state.messages) > max_history:
            st.session_state.messages = st.session_state.messages[-max_history:]

    def process_user_query(self, query: str) -> bool:
        """
        Process a user query and generate a response.

        Args:
            query: User's question

        Returns:
            True if successful, False otherwise
        """
        # Add user message
        self.add_message("user", query)

        # Check if pipeline is ready
        if not st.session_state.pipeline_initialized:
            self.add_message(
                "error",
                "The knowledge base is not ready yet. Please wait for initialization or refresh the page."
            )
            return False

        # Check API key
        if not self.api_key_configured:
            self.add_message(
                "error",
                "Groq API key is not configured. Please add GROQ_API_KEY to your secrets."
            )
            return False

        try:
            # Retrieve relevant context
            retrieval_result = self.rag_pipeline.query(query)

            # Generate response
            llm_response = self.llm_handler.answer_question(query, retrieval_result)

            # Add assistant message
            self.add_message(
                "assistant",
                llm_response.content,
                llm_response.sources,
            )

            return True

        except Exception as e:
            logger.error(f"Error processing query: {e}")
            self.add_message(
                "error",
                f"Sorry, I encountered an error: {str(e)}"
            )
            return False

    def render(self):
        """Render the complete chat interface."""
        # Inject custom CSS
        inject_custom_css()

        # Page config
        st.set_page_config(
            page_title=self.ui_config.app_title,
            page_icon="🤖",
            layout="centered",
            initial_sidebar_state="expanded",
        )

        # Render sidebar
        render_sidebar()

        # Main header
        render_header(
            show_clear_button=True,
            on_clear=self.clear_chat,
            status_text="Ready" if self.api_key_configured else "API Key Missing",
            status_color="green" if self.api_key_configured else "red",
        )

        # Initialize pipeline if not done
        if not st.session_state.pipeline_initialized:
            if not self.initialize_pipeline():
                render_error_state(st.session_state.initialization_error or "Initialization failed")
                return

        # Show welcome message if no messages
        if not st.session_state.messages:
            render_welcome_message()

        # Render message history
        for msg in st.session_state.messages:
            with st.container():
                render_message(
                    role=msg.role,
                    content=msg.content,
                    sources=msg.sources if msg.role == "assistant" else None,
                )

        # Render input area
        user_input = render_input_area(
            placeholder="Ask about academic policies...",
            disabled=not self.api_key_configured or not st.session_state.pipeline_initialized,
        )

        # Process user input
        if user_input:
            # Show processing indicator
            with st.spinner("Thinking..."):
                self.process_user_query(user_input)

            # Rerun to display the response
            st.rerun()

        # Render footer
        render_footer()


def run_chat_interface():
    """Entry point for running the chat interface."""
    chat = ChatInterface()
    chat.render()


if __name__ == "__main__":
    run_chat_interface()
