"""
Z.M.ai - UI Styles

CSS styling for the Streamlit application.
Adapted from the React frontend design with glassmorphism effects.
"""

from config import get_ui_config

# Get configuration for dynamic colors
ui_config = get_ui_config()

# Color palette
COLORS = {
    "primary_start": "#6366f1",    # Indigo
    "primary_mid": ui_config.theme_color,  # Configurable purple (default: #8b5cf6)
    "primary_end": "#d946ef",      # Fuchsia
    "accent_glow": "rgba(139, 92, 246, 0.4)",
    "bg_primary": "#fafafa",
    "bg_secondary": "#f5f5f7",
    "bg_glass": "rgba(255, 255, 255, 0.85)",
    "bg_glass_strong": "rgba(255, 255, 255, 0.95)",
    "text_primary": "#111111",
    "text_secondary": "#6b7280",
    "text_tertiary": "#9ca3af",
    "border_subtle": "rgba(0, 0, 0, 0.06)",
    "border_medium": "rgba(0, 0, 0, 0.1)",
    "success": "#10b981",
    "error": "#ef4444",
    "warning": "#f59e0b",
}


def get_gradient_css() -> str:
    """Get the animated gradient background CSS."""
    return f"""
    <style>
        /* Main app background */
        .stApp {{
            background: linear-gradient(135deg, {COLORS["primary_start"]}, {COLORS["primary_mid"]}, {COLORS["primary_end"]}, #667eea, #764ba2);
            background-size: 400% 400%;
            animation: gradientShift 15s ease infinite;
        }}

        @keyframes gradientShift {{
            0% {{ background-position: 0% 50%; }}
            25% {{ background-position: 100% 50%; }}
            50% {{ background-position: 100% 100%; }}
            75% {{ background-position: 0% 100%; }}
            100% {{ background-position: 0% 50%; }}
        }}

        /* Hide default Streamlit background */
        .stApp >> div[data-testid="stAppViewContainer"] > div > div {{
            background: transparent;
        }}
    </style>
    """


def get_glassmorphism_css() -> str:
    """Get glassmorphism effect CSS."""
    return f"""
    <style>
        /* Glassmorphism container */
        .glass-container {{
            background: {COLORS["bg_glass_strong"]};
            backdrop-filter: blur(20px) saturate(180%);
            -webkit-backdrop-filter: blur(20px) saturate(180%);
            border-radius: 16px;
            border: 1px solid {COLORS["border_subtle"]};
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.07), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
        }}

        /* Glassmorphic header */
        .glass-header {{
            background: {COLORS["bg_glass_strong"]};
            backdrop-filter: blur(20px) saturate(180%);
            -webkit-backdrop-filter: blur(20px) saturate(180%);
            border-bottom: 1px solid {COLORS["border_subtle"]};
            box-shadow: 0 1px 2px rgba(0, 0, 0, 0.05);
        }}

        /* Glassmorphic input area */
        .glass-input {{
            background: {COLORS["bg_glass_strong"]};
            backdrop-filter: blur(20px) saturate(180%);
            -webkit-backdrop-filter: blur(20px) saturate(180%);
            border-top: 1px solid {COLORS["border_subtle"]};
        }}
    </style>
    """


def get_message_css() -> str:
    """Get message bubble styling CSS."""
    return f"""
    <style>
        /* Message containers */
        .message-container {{
            display: flex;
            gap: 14px;
            padding: 16px 20px;
            animation: messageSlide 0.4s cubic-bezier(0.34, 1.56, 0.64, 1);
        }}

        @keyframes messageSlide {{
            from {{
                opacity: 0;
                transform: translateY(20px) scale(0.98);
            }}
            to {{
                opacity: 1;
                transform: translateY(0) scale(1);
            }}
        }}

        /* User message */
        .message-user {{
            background: linear-gradient(135deg, {COLORS["primary_start"]}, {COLORS["primary_mid"]});
            color: white;
            padding: 12px 18px;
            border-radius: 18px 18px 4px 18px;
            box-shadow: 0 4px 15px {COLORS["accent_glow"]};
            max-width: 80%;
            margin-left: auto;
        }}

        /* Assistant message */
        .message-assistant {{
            background: white;
            color: {COLORS["text_primary"]};
            padding: 12px 18px;
            border-radius: 18px 18px 18px 4px;
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
            max-width: 80%;
        }}

        /* Error message */
        .message-error {{
            background: rgba(239, 68, 68, 0.1);
            color: {COLORS["error"]};
            padding: 12px 18px;
            border-radius: 12px;
            border-left: 4px solid {COLORS["error"]};
        }}
    </style>
    """


def get_source_tag_css() -> str:
    """Get source tag styling CSS."""
    return f"""
    <style>
        /* Source tags */
        .source-tag {{
            background: linear-gradient(135deg, {COLORS["primary_start"]}, {COLORS["primary_mid"]});
            color: white;
            padding: 6px 12px;
            border-radius: 9999px;
            font-size: 11px;
            font-weight: 600;
            display: inline-block;
            margin: 4px 4px 4px 0;
            box-shadow: 0 2px 8px {COLORS["accent_glow"]};
            transition: all 0.25s ease;
        }}

        .source-tag:hover {{
            transform: translateY(-2px);
            box-shadow: 0 4px 12px {COLORS["accent_glow"]};
        }}

        .sources-container {{
            margin-top: 12px;
            padding-top: 12px;
            border-top: 1px solid {COLORS["border_subtle"]};
        }}
    </style>
    """


def get_typing_indicator_css() -> str:
    """Get typing indicator animation CSS."""
    return f"""
    <style>
        /* Typing indicator */
        .typing-indicator {{
            display: flex;
            gap: 6px;
            padding: 12px 0;
        }}

        .typing-dot {{
            width: 10px;
            height: 10px;
            border-radius: 50%;
            background: linear-gradient(135deg, {COLORS["primary_start"]}, {COLORS["primary_mid"]});
            animation: typingBounce 1.4s infinite ease-in-out;
            box-shadow: 0 0 10px {COLORS["accent_glow"]};
        }}

        .typing-dot:nth-child(2) {{
            animation-delay: 0.15s;
        }}

        .typing-dot:nth-child(3) {{
            animation-delay: 0.3s;
        }}

        @keyframes typingBounce {{
            0%, 80%, 100% {{
                transform: scale(0.6);
                opacity: 0.4;
            }}
            40% {{
                transform: scale(1);
                opacity: 1;
            }}
        }}
    </style>
    """


def get_custom_scrollbar_css() -> str:
    """Get custom scrollbar CSS."""
    return f"""
    <style>
        /* Custom scrollbar for messages */
        [data-testid="stVerticalBlock"] > div > div > div > div {{
            scrollbar-width: thin;
            scrollbar-color: {COLORS["primary_mid"]} transparent;
        }}

        [data-testid="stVerticalBlock"] > div > div > div > div::-webkit-scrollbar {{
            width: 8px;
        }}

        [data-testid="stVerticalBlock"] > div > div > div > div::-webkit-scrollbar-track {{
            background: transparent;
        }}

        [data-testid="stVerticalBlock"] > div > div > div > div::-webkit-scrollbar-thumb {{
            background: linear-gradient(180deg, {COLORS["primary_start"]}, {COLORS["primary_mid"]});
            border-radius: 9999px;
            border: 2px solid transparent;
            background-clip: content-box;
        }}

        [data-testid="stVerticalBlock"] > div > div > div > div::-webkit-scrollbar-thumb:hover {{
            background: linear-gradient(180deg, {COLORS["primary_mid"]}, {COLORS["primary_end"]});
            background-clip: content-box;
        }}
    </style>
    """


def get_all_css() -> str:
    """
    Combine all CSS into a single string for injection.

    Returns:
        Complete CSS string for use in st.markdown()
    """
    return "".join([
        get_gradient_css(),
        get_glassmorphism_css(),
        get_message_css(),
        get_source_tag_css(),
        get_typing_indicator_css(),
        get_custom_scrollbar_css(),
    ])


def inject_custom_css():
    """
    Inject all custom CSS into the Streamlit app.
    Call this once at the beginning of your app.
    """
    import streamlit as st
    st.markdown(get_all_css(), unsafe_allow_html=True)


def format_user_message(content: str) -> str:
    """Format a user message for display."""
    return f"""
    <div class="message-container">
        <div class="message-user">
            {content}
        </div>
    </div>
    """


def format_assistant_message(content: str, sources: list = None) -> str:
    """
    Format an assistant message for display.

    Args:
        content: Message content (can include markdown)
        sources: Optional list of source strings

    Returns:
        HTML formatted message
    """
    # Convert markdown to HTML (basic conversion)
    # Note: For full markdown support, use st.markdown() separately
    formatted_content = content.replace("\n", "<br>")

    source_html = ""
    if sources:
        source_tags = "".join([f'<span class="source-tag">{source}</span>' for source in sources])
        source_html = f'<div class="sources-container">{source_tags}</div>'

    return f"""
    <div class="message-container">
        <div class="message-assistant">
            {formatted_content}
            {source_html}
        </div>
    </div>
    """


def format_error_message(content: str) -> str:
    """Format an error message for display."""
    return f"""
    <div class="message-container">
        <div class="message-error">
            {content}
        </div>
    </div>
    """


def get_typing_indicator_html() -> str:
    """Get HTML for a typing indicator."""
    return """
    <div class="typing-indicator">
        <div class="typing-dot"></div>
        <div class="typing-dot"></div>
        <div class="typing-dot"></div>
    </div>
    """
