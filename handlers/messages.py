"""
Message handlers for processing text, voice, and image messages.
"""

import logging
import io
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, MessageHandler, filters

from config import settings
from locales import get_text
from database import DatabaseOperations
from services import AIService, SubscriptionService, MediaService
from utils import RateLimiter

logger = logging.getLogger(__name__)


async def handle_text_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle incoming text messages and generate AI responses."""
    user = update.effective_user
    message = update.message

    db_ops: DatabaseOperations = context.bot_data["db_ops"]
    ai_service: AIService = context.bot_data["ai_service"]
    sub_service: SubscriptionService = context.bot_data["sub_service"]
    rate_limiter: RateLimiter = context.bot_data["rate_limiter"]

    # Get user data
    user_data = await db_ops.get_user(user.id)
    if not user_data:
        await db_ops.create_user(user.id, user.username, user.first_name, user.last_name)
        user_data = await db_ops.get_user(user.id)

    lang = user_data.get("language_code", "en")

    # Check if banned
    if user_data.get("is_banned"):
        await message.reply_text(get_text("banned", lang))
        return
    
    # Check rate limit
    is_premium = user_data.get("is_premium", False)
    can_send, current, limit = await rate_limiter.check_limit(user.id, is_premium)
    
    if not can_send:
        await message.reply_text(get_text("rate_limited", lang))
        return
    
    # Record request
    await rate_limiter.record_request(user.id)
    
    # Send thinking indicator
    thinking_msg = await message.reply_text(get_text("thinking", lang))
    
    try:
        # Get conversation history
        history = await db_ops.get_conversation_history(user.id, limit=settings.max_context_messages)
        formatted_history = [
            {"role": msg["role"], "content": msg["content"]}
            for msg in history
        ]
        
        # Save user message
        await db_ops.add_message(user.id, "user", message.text)
        
        # Generate AI response
        model = user_data.get("preferred_model", settings.default_ai_model)
        response, model_used, tokens = await ai_service.generate_response(
            user_message=message.text,
            conversation_history=formatted_history,
            model=model
        )
        
        # Save AI response
        await db_ops.add_message(user.id, "assistant", response, model_used, tokens)
        
        # Update stats
        await db_ops.increment_message_count(user.id, tokens)
        await db_ops.increment_stats(
            messages=1,
            openai_requests=0,
            gemini_requests=1,
            tokens=tokens
        )
        
        # Delete thinking message and send response
        await thinking_msg.delete()
        
        # Split long messages
        if len(response) > 4096:
            for i in range(0, len(response), 4096):
                await message.reply_text(response[i:i+4096])
        else:
            await message.reply_text(response)
        
        logger.info(f"User {user.id}: processed message, {tokens} tokens, model: {model_used}")
        
    except Exception as e:
        logger.error(f"Error processing message for user {user.id}: {e}")
        await thinking_msg.edit_text(get_text("error_general", lang))
        await db_ops.log_error("message_processing", str(e), user_id=user.id)


async def handle_voice_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle voice messages by transcribing and processing."""
    user = update.effective_user
    message = update.message
    
    db_ops: DatabaseOperations = context.bot_data["db_ops"]
    ai_service: AIService = context.bot_data["ai_service"]
    media_service: MediaService = context.bot_data["media_service"]
    sub_service: SubscriptionService = context.bot_data["sub_service"]
    
    user_data = await db_ops.get_user(user.id)
    lang = user_data.get("language_code", "en") if user_data else "en"
    
    # Check if premium for voice (admins bypass)
    sub_info = await sub_service.get_subscription_info(user.id)
    is_admin = user.id == settings.admin_user_id
    if not sub_info["is_premium"] and not is_admin:
        await message.reply_text(
            "🎤 Voice messages require Premium subscription.\nUse /subscribe to upgrade!"
        )
        return
    
    thinking_msg = await message.reply_text("🎤 Transcribing voice message...")
    
    try:
        # Download voice file
        voice_file = await message.voice.get_file()
        voice_data = await media_service.download_voice_message(voice_file)
        
        # Transcribe
        transcribed_text = await ai_service.transcribe_audio(voice_data)
        
        if not transcribed_text:
            await thinking_msg.edit_text("❌ Could not transcribe voice message.")
            return
        
        # Process as text message
        await thinking_msg.edit_text(get_text("thinking", lang))
        
        # Get conversation history
        history = await db_ops.get_conversation_history(user.id)
        formatted_history = [{"role": m["role"], "content": m["content"]} for m in history]
        
        # Save transcribed message
        full_text = f"[Voice message]: {transcribed_text}"
        await db_ops.add_message(user.id, "user", full_text)
        
        # Generate response
        model = user_data.get("preferred_model", settings.default_ai_model)
        response, model_used, tokens = await ai_service.generate_response(
            transcribed_text, formatted_history, model
        )
        
        await db_ops.add_message(user.id, "assistant", response, model_used, tokens)
        await db_ops.increment_message_count(user.id, tokens)
        await db_ops.increment_stats(messages=1, tokens=tokens)
        
        await thinking_msg.delete()
        await message.reply_text(
            get_text("voice_transcribed", lang, text=transcribed_text[:100]) + response
        )
        
    except Exception as e:
        logger.error(f"Voice message error: {e}")
        await thinking_msg.edit_text(get_text("error_general", lang))


async def handle_photo_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle photo messages with vision capabilities."""
    user = update.effective_user
    message = update.message

    db_ops: DatabaseOperations = context.bot_data["db_ops"]
    ai_service: AIService = context.bot_data["ai_service"]
    media_service: MediaService = context.bot_data["media_service"]
    sub_service: SubscriptionService = context.bot_data["sub_service"]

    user_data = await db_ops.get_user(user.id)
    lang = user_data.get("language_code", "en") if user_data else "en"

    # Check if premium for images (admins bypass)
    sub_info = await sub_service.get_subscription_info(user.id)
    is_admin = user.id == settings.admin_user_id
    if not sub_info["is_premium"] and not is_admin:
        await message.reply_text(
            "📸 Image analysis requires Premium subscription.\nUse /subscribe to upgrade!"
        )
        return

    thinking_msg = await message.reply_text(get_text("image_received", lang))

    try:
        # Get the largest photo
        photo = message.photo[-1]
        photo_file = await photo.get_file()
        image_data = await media_service.download_image(photo_file)

        # Get caption or use default prompt
        prompt = message.caption or "Describe this image in detail."

        # Analyze image
        response, model_used, tokens = await ai_service.analyze_image(
            image_data, prompt
        )

        # Save to history
        await db_ops.add_message(user.id, "user", f"[Image with prompt]: {prompt}")
        await db_ops.add_message(user.id, "assistant", response, model_used, tokens)
        await db_ops.increment_message_count(user.id, tokens)
        await db_ops.increment_stats(messages=1, tokens=tokens)

        await thinking_msg.delete()
        await message.reply_text(response)

    except Exception as e:
        logger.error(f"Photo message error: {e}")
        await thinking_msg.edit_text(get_text("error_general", lang))


def setup_message_handlers(app) -> None:
    """Register message handlers."""
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text_message))
    app.add_handler(MessageHandler(filters.VOICE, handle_voice_message))
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo_message))
