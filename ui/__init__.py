"""
Z.M.ai - UI Module

This module contains the UI components and styling for the application.
"""

from .styles import (
    COLORS,
    get_all_css,
    inject_custom_css,
    format_user_message,
    format_assistant_message,
    format_error_message,
    get_typing_indicator_html,
)
from .components import (
    render_header,
    render_welcome_message,
    render_message,
    render_typing_indicator,
    render_input_area,
    render_sidebar,
    render_footer,
    render_error_state,
    render_loading_state,
)
from .chat_interface import (
    ChatMessage,
    ChatInterface,
    run_chat_interface,
)

__all__ = [
    "COLORS",
    "get_all_css",
    "inject_custom_css",
    "format_user_message",
    "format_assistant_message",
    "format_error_message",
    "get_typing_indicator_html",
    "render_header",
    "render_welcome_message",
    "render_message",
    "render_typing_indicator",
    "render_input_area",
    "render_sidebar",
    "render_footer",
    "render_error_state",
    "render_loading_state",
    "ChatMessage",
    "ChatInterface",
    "run_chat_interface",
]
