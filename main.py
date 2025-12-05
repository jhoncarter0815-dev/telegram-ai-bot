"""
Telegram AI Bot - Main Entry Point

A comprehensive Telegram bot powered by ChatGPT and Gemini AI.
Features:
- Dual AI integration (OpenAI + Google Gemini)
- Telegram Stars subscription system
- Multi-language support
- Voice and image processing
- Admin panel with statistics

Author: AI Assistant Bot
"""

import asyncio
import logging
from telegram import Update
from telegram.ext import Application, ContextTypes
from telegram.request import HTTPXRequest

from config import settings
from database import Database, DatabaseOperations
from services import AIService, SubscriptionService, MediaService
from utils import setup_logging, RateLimiter
from handlers import (
    setup_command_handlers,
    setup_message_handlers,
    setup_callback_handlers,
    setup_admin_handlers,
    setup_payment_handlers
)

# Initialize logging
logger = setup_logging()


async def post_init(application: Application) -> None:
    """Initialize services after bot starts."""
    logger.info("Initializing bot services...")
    
    # Initialize database
    db = Database(settings.database_path)
    await db.connect()
    db_ops = DatabaseOperations(db)
    
    # Initialize services
    ai_service = AIService()
    sub_service = SubscriptionService(db_ops)
    media_service = MediaService()
    rate_limiter = RateLimiter(
        default_limit=settings.free_tier_limit,
        premium_limit=settings.premium_tier_limit
    )
    
    # Store in bot_data for access in handlers
    application.bot_data["db"] = db
    application.bot_data["db_ops"] = db_ops
    application.bot_data["ai_service"] = ai_service
    application.bot_data["sub_service"] = sub_service
    application.bot_data["media_service"] = media_service
    application.bot_data["rate_limiter"] = rate_limiter
    
    # Check expired subscriptions
    expired = await sub_service.check_and_expire_subscriptions()
    if expired:
        logger.info(f"Expired {len(expired)} subscriptions")
    
    logger.info("Bot services initialized successfully")


async def post_shutdown(application: Application) -> None:
    """Cleanup when bot shuts down."""
    logger.info("Shutting down bot services...")
    
    # Close database connection
    if "db" in application.bot_data:
        await application.bot_data["db"].close()
    
    # Close media service
    if "media_service" in application.bot_data:
        await application.bot_data["media_service"].close()
    
    logger.info("Bot services shut down successfully")


async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Global error handler for unhandled exceptions."""
    import traceback
    error_trace = ''.join(traceback.format_exception(type(context.error), context.error, context.error.__traceback__))
    logger.error(f"Exception while handling update: {context.error}\n{error_trace}")

    # Log to database if available
    if "db_ops" in context.bot_data:
        user_id = None
        if isinstance(update, Update) and update.effective_user:
            user_id = update.effective_user.id

        try:
            await context.bot_data["db_ops"].log_error(
                error_type=type(context.error).__name__,
                error_message=str(context.error)[:500],
                user_id=user_id
            )
        except Exception as db_err:
            logger.error(f"Failed to log error to database: {db_err}")

    # Notify user of error with details for debugging
    if isinstance(update, Update) and update.effective_message:
        try:
            error_msg = str(context.error)[:200]
            await update.effective_message.reply_text(
                f"❌ Error: {error_msg}"
            )
        except Exception:
            pass


async def periodic_tasks(application: Application) -> None:
    """Run periodic maintenance tasks."""
    while True:
        await asyncio.sleep(3600)  # Run every hour
        
        try:
            if "sub_service" in application.bot_data:
                expired = await application.bot_data["sub_service"].check_and_expire_subscriptions()
                if expired:
                    logger.info(f"Periodic check: expired {len(expired)} subscriptions")
            
            if "rate_limiter" in application.bot_data:
                await application.bot_data["rate_limiter"].cleanup_old_entries()
                logger.debug("Rate limiter cleanup completed")
        except Exception as e:
            logger.error(f"Error in periodic tasks: {e}")


def main() -> None:
    """Main function to start the bot."""
    logger.info("=" * 50)
    logger.info("Starting Telegram AI Bot...")
    logger.info(f"Admin User ID: {settings.admin_user_id}")
    logger.info("=" * 50)
    
    # Configure HTTP request with longer timeouts
    request = HTTPXRequest(
        connect_timeout=30.0,
        read_timeout=30.0,
        write_timeout=30.0,
        pool_timeout=30.0
    )

    # Build application
    application = (
        Application.builder()
        .token(settings.telegram_bot_token)
        .request(request)
        .post_init(post_init)
        .post_shutdown(post_shutdown)
        .build()
    )
    
    # Register handlers
    setup_command_handlers(application)
    setup_message_handlers(application)
    setup_callback_handlers(application)
    setup_admin_handlers(application)
    setup_payment_handlers(application)
    
    # Register error handler
    application.add_error_handler(error_handler)
    
    # Run the bot
    logger.info("Bot is starting polling...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
