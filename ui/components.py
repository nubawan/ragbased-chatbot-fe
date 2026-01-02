"""
Z.M.ai - UI Components

Reusable UI components for the Streamlit application.
"""

import logging
from typing import Optional, List, Callable

import streamlit as st

from config import get_ui_config
from .styles import (
    COLORS,
    format_user_message,
    format_assistant_message,
    format_error_message,
    get_typing_indicator_html,
)

logger = logging.getLogger(__name__)


def render_header(
    show_clear_button: bool = True,
    on_clear: Optional[Callable] = None,
    status_text: str = "Ready",
    status_color: str = "green",
) -> None:
    """
    Render the application header.

    Args:
        show_clear_button: Whether to show the clear chat button
        on_clear: Optional callback when clear is clicked
        status_text: Status text to display
        status_color: Color of the status indicator (green, red, amber)
    """
    ui_config = get_ui_config()

    # Header container
    col1, col2, col3 = st.columns([2, 1, 1])

    with col1:
        # Logo and title
        st.markdown(f"""
        <div style="display: flex; align-items: center; gap: 12px;">
            <div style="
                background: linear-gradient(135deg, {COLORS["primary_start"]}, {COLORS["primary_mid"]}, {COLORS["primary_end"]});
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
                font-size: 24px;
                font-weight: 700;
                letter-spacing: -0.02em;
            ">
                {ui_config.app_title}
            </div>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        # Status indicator
        status_colors = {
            "green": COLORS["success"],
            "red": COLORS["error"],
            "amber": COLORS["warning"],
        }
        dot_color = status_colors.get(status_color, COLORS["success"])

        st.markdown(f"""
        <div style="
            display: flex;
            align-items: center;
            gap: 8px;
            padding: 8px 14px;
            background: {COLORS["bg_secondary"]};
            border-radius: 9999px;
            font-size: 13px;
        ">
            <div style="
                width: 10px;
                height: 10px;
                border-radius: 50%;
                background: {dot_color};
                box-shadow: 0 0 12px {dot_color}40;
            "></div>
            <span style="color: {COLORS["text_secondary"]};">{status_text}</span>
        </div>
        """, unsafe_allow_html=True)

    with col3:
        # Clear button
        if show_clear_button:
            if st.button("Clear Chat", key="header_clear", use_container_width=True):
                if on_clear:
                    on_clear()
                st.rerun()


def render_welcome_message() -> None:
    """Render the welcome message shown to new users."""
    ui_config = get_ui_config()

    st.markdown(f"""
    <div style="
        text-align: center;
        padding: 40px 20px;
        animation: messageSlide 0.4s cubic-bezier(0.34, 1.56, 0.64, 1);
    ">
        <div style="
            background: linear-gradient(135deg, {COLORS["primary_start"]}, {COLORS["primary_mid"]}, {COLORS["primary_end"]});
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            font-size: 32px;
            font-weight: 700;
            margin-bottom: 16px;
        ">
            Welcome to {ui_config.app_title}!
        </div>
        <div style="color: {COLORS["text_secondary"]}; font-size: 16px; line-height: 1.6;">
            {ui_config.app_subtitle}
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Display welcome message content
    st.markdown(ui_config.welcome_message)


def render_message(
    role: str,
    content: str,
    sources: Optional[List[str]] = None,
    show_avatar: bool = True,
) -> None:
    """
    Render a chat message.

    Args:
        role: "user" or "assistant"
        content: Message content (markdown supported)
        sources: Optional list of source citations
        show_avatar: Whether to show avatar
    """
    if role == "user":
        st.markdown(format_user_message(content), unsafe_allow_html=True)
    elif role == "assistant":
        # Use st.markdown for proper markdown rendering
        st.markdown(content, unsafe_allow_html=True)

        # Add sources if present
        if sources:
            source_tags = "".join([f'<span class="source-tag">{s}</span>' for s in sources])
            st.markdown(f"""
            <div class="sources-container" style="margin-top: 16px;">
                <div style="font-size: 12px; color: {COLORS['text_tertiary']}; font-weight: 500; margin-bottom: 8px;">
                    SOURCES:
                </div>
                {source_tags}
            </div>
            """, unsafe_allow_html=True)
    elif role == "error":
        st.markdown(format_error_message(content), unsafe_allow_html=True)


def render_typing_indicator() -> None:
    """Render a typing indicator to show the bot is thinking."""
    st.markdown(get_typing_indicator_html(), unsafe_allow_html=True)


def render_input_area(
    placeholder: str = "Ask about academic policies...",
            disabled: bool = False,
) -> str:
    """
    Render the chat input area.

    Args:
        placeholder: Input placeholder text
        disabled: Whether input is disabled

    Returns:
        User input text
    """
    # Use Streamlit's chat input
    user_input = st.chat_input(
        placeholder=placeholder,
        disabled=disabled,
    )

    return user_input or ""


def render_sidebar(
    api_key_configured: bool = True,
    show_settings: bool = True,
) -> dict:
    """
    Render the sidebar with settings and info.

    Args:
        api_key_configured: Whether API key is configured
        show_settings: Whether to show settings section

    Returns:
        Dictionary of sidebar values
    """
    with st.sidebar:
        st.markdown(f"""
        <div style="
            text-align: center;
            padding: 20px 0;
            margin-bottom: 20px;
            border-bottom: 1px solid {COLORS['border_subtle']};
        ">
            <div style="
                background: linear-gradient(135deg, {COLORS['primary_start']}, {COLORS['primary_mid']}, {COLORS['primary_end']});
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
                font-size: 20px;
                font-weight: 700;
            ">
                {get_ui_config().app_title}
            </div>
        </div>
        """, unsafe_allow_html=True)

        result = {}

        # API Key status
        st.subheader("Configuration")
        if api_key_configured:
            st.success("Groq API Key: Configured")
        else:
            st.error("Groq API Key: Missing")
            st.info("Please add GROQ_API_KEY to:")
            st.code(".streamlit/secrets.toml")

        result["api_key_configured"] = api_key_configured

        if show_settings:
            st.subheader("Settings")

            # Model selection (future feature)
            result["model"] = st.selectbox(
                "Model",
                ["llama-3.1-8b-instant", "llama-3.1-70b-versatile", "mixtral-8x7b-32768"],
                index=0,
                disabled=True,  # For future implementation
                help="Model selection coming soon",
            )

            # Data sources info
            st.subheader("Data Sources")
            st.info("""
            **PDF Documents**
            Academic Policy Manual

            **Website**
            iqra.edu.pk/iu-policies/
            """)

        # About section
        st.markdown("---")
        st.markdown("""
        <div style="text-align: center; padding: 20px 0;">
            <div style="font-size: 12px; color: {COLORS['text_tertiary']};">
                <strong>{app_title}</strong><br>
                RAG-based Policy Assistant<br>
                <br>
                Built with Streamlit + Groq
            </div>
        </div>
        """.format(app_title=get_ui_config().app_title, **COLORS), unsafe_allow_html=True)

    return result


def render_footer() -> None:
    """Render the footer with attribution."""
    st.markdown(f"""
    <div style="
        text-align: center;
        padding: 20px;
        color: {COLORS['text_tertiary']};
        font-size: 12px;
    ">
        Powered by {get_ui_config().app_title} • RAG-based Academic Policy Assistant
    </div>
    """, unsafe_allow_html=True)


def render_error_state(error_message: str) -> None:
    """
    Render an error state when something goes wrong.

    Args:
        error_message: Error message to display
    """
    st.markdown(f"""
    <div style="
        text-align: center;
        padding: 60px 20px;
        background: {COLORS['bg_glass']};
        border-radius: 16px;
        margin: 20px 0;
    ">
        <div style="font-size: 48px; margin-bottom: 16px;">⚠️</div>
        <div style="font-size: 18px; font-weight: 600; color: {COLORS['error']}; margin-bottom: 8px;">
            Oops! Something went wrong
        </div>
        <div style="color: {COLORS['text_secondary']};">
            {error_message}
        </div>
    </div>
    """, unsafe_allow_html=True)


def render_loading_state(message: str = "Loading...") -> None:
    """
    Render a loading state.

    Args:
        message: Loading message to display
    """
    st.markdown(f"""
    <div style="
        text-align: center;
        padding: 60px 20px;
    ">
        <div class="typing-indicator" style="justify-content: center; margin-bottom: 20px;">
            <div class="typing-dot"></div>
            <div class="typing-dot"></div>
            <div class="typing-dot"></div>
        </div>
        <div style="color: {COLORS['text_secondary']};">
            {message}
        </div>
    </div>
    """, unsafe_allow_html=True)
