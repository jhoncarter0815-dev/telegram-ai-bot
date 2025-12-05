"""
Configuration settings module.
Loads environment variables and provides centralized configuration.
"""

import os
from dataclasses import dataclass
from typing import Optional
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


@dataclass
class Settings:
    """Application settings loaded from environment variables."""
    
    # Telegram Configuration
    telegram_bot_token: str = os.getenv("TELEGRAM_BOT_TOKEN", "")
    admin_user_id: int = int(os.getenv("ADMIN_USER_ID", "0"))
    
    # AI API Keys
    gemini_api_key: str = os.getenv("GEMINI_API_KEY", "")
    
    # Database
    database_url: str = os.getenv("DATABASE_URL", "sqlite:///bot_database.db")
    
    # Rate Limiting
    free_tier_limit: int = int(os.getenv("FREE_TIER_LIMIT", "20"))
    premium_tier_limit: int = int(os.getenv("PREMIUM_TIER_LIMIT", "1000"))
    
    # Subscription Prices (Telegram Stars)
    subscription_price_monthly: int = int(os.getenv("SUBSCRIPTION_PRICE_MONTHLY", "100"))
    subscription_price_yearly: int = int(os.getenv("SUBSCRIPTION_PRICE_YEARLY", "1000"))
    
    # Logging
    log_level: str = os.getenv("LOG_LEVEL", "INFO")
    log_file: str = os.getenv("LOG_FILE", "bot.log")
    
    # AI Model Defaults
    default_ai_model: str = "gemini-2.0-flash"
    default_gemini_model: str = "gemini-2.0-flash"
    
    # Context Settings
    max_context_messages: int = 20
    max_message_length: int = 4096
    
    # Supported Languages
    supported_languages: tuple = ("en", "ru", "es", "fr", "de", "zh", "ar", "hi", "pt", "ja")
    default_language: str = "en"
    
    def validate(self) -> bool:
        """Validate required settings are present."""
        required = [
            self.telegram_bot_token,
            self.admin_user_id,
        ]
        return all(required) and self.admin_user_id > 0
    
    @property
    def database_path(self) -> str:
        """Extract database file path from URL."""
        if self.database_url.startswith("sqlite:///"):
            return self.database_url.replace("sqlite:///", "")
        return "bot_database.db"


# Global settings instance
settings = Settings()

# Validate settings on import
if not settings.validate():
    raise ValueError(
        "Missing required configuration. Please check your .env file."
    )

