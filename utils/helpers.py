"""
Helper utility functions for common operations.
"""

import re
from datetime import datetime
from typing import Optional


def escape_markdown(text: str, version: int = 2) -> str:
    """
    Escape special characters for Telegram MarkdownV2.
    
    Args:
        text: Text to escape
        version: Markdown version (1 or 2)
    
    Returns:
        Escaped text safe for Telegram
    """
    if version == 2:
        # Characters that need escaping in MarkdownV2
        escape_chars = r'_*[]()~`>#+-=|{}.!'
        return re.sub(f'([{re.escape(escape_chars)}])', r'\\\1', text)
    else:
        # Markdown V1
        escape_chars = r'_*`['
        return re.sub(f'([{re.escape(escape_chars)}])', r'\\\1', text)


def truncate_text(text: str, max_length: int = 4096, suffix: str = "...") -> str:
    """
    Truncate text to a maximum length.
    
    Args:
        text: Text to truncate
        max_length: Maximum allowed length
        suffix: Suffix to add if truncated
    
    Returns:
        Truncated text
    """
    if len(text) <= max_length:
        return text
    return text[:max_length - len(suffix)] + suffix


def format_timestamp(
    timestamp: Optional[str],
    format_str: str = "%Y-%m-%d %H:%M"
) -> str:
    """
    Format a timestamp string for display.
    
    Args:
        timestamp: ISO format timestamp string
        format_str: Desired output format
    
    Returns:
        Formatted date string
    """
    if not timestamp:
        return "N/A"
    try:
        dt = datetime.fromisoformat(timestamp)
        return dt.strftime(format_str)
    except (ValueError, TypeError):
        return timestamp


def format_number(num: int) -> str:
    """Format large numbers with commas."""
    return f"{num:,}"


def format_duration(seconds: int) -> str:
    """Format duration in human-readable format."""
    if seconds < 60:
        return f"{seconds}s"
    elif seconds < 3600:
        minutes = seconds // 60
        return f"{minutes}m"
    elif seconds < 86400:
        hours = seconds // 3600
        return f"{hours}h"
    else:
        days = seconds // 86400
        return f"{days}d"


def parse_user_id(text: str) -> Optional[int]:
    """
    Parse user ID from text input.
    Handles both numeric IDs and @username mentions.
    
    Args:
        text: Text that might contain a user ID
    
    Returns:
        User ID as integer or None
    """
    text = text.strip()
    
    # Direct numeric ID
    if text.isdigit():
        return int(text)
    
    # Try to extract numbers
    numbers = re.findall(r'\d+', text)
    if numbers:
        return int(numbers[0])
    
    return None


def split_message(text: str, max_length: int = 4096) -> list[str]:
    """
    Split a long message into multiple parts.
    
    Args:
        text: Text to split
        max_length: Maximum length per message
    
    Returns:
        List of message parts
    """
    if len(text) <= max_length:
        return [text]
    
    parts = []
    current = ""
    
    for line in text.split('\n'):
        if len(current) + len(line) + 1 <= max_length:
            current += line + '\n'
        else:
            if current:
                parts.append(current.strip())
            current = line + '\n'
    
    if current:
        parts.append(current.strip())
    
    return parts


def clean_html(text: str) -> str:
    """Remove HTML tags from text."""
    return re.sub(r'<[^>]+>', '', text)


def get_display_name(
    first_name: str = None,
    last_name: str = None,
    username: str = None
) -> str:
    """Get a display name from user info."""
    if first_name and last_name:
        return f"{first_name} {last_name}"
    elif first_name:
        return first_name
    elif username:
        return f"@{username}"
    return "Unknown User"

