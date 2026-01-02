"""
Z.M.ai - Main Application Entry Point

A RAG-based academic policy chatbot powered by Streamlit and Groq.
"""

import logging
import sys

from ui.chat_interface import run_chat_interface

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    stream=sys.stdout,
)

logger = logging.getLogger(__name__)


def main():
    """Main entry point for the Z.M.ai application."""
    logger.info("Starting Z.M.ai application...")

    try:
        run_chat_interface()
    except KeyboardInterrupt:
        logger.info("Application interrupted by user")
    except Exception as e:
        logger.exception(f"Unexpected error: {e}")
        raise


if __name__ == "__main__":
    main()
