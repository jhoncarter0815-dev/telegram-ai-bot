"""
Command handlers for user-facing bot commands.
"""

import logging
from datetime import datetime, timedelta
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CommandHandler

from config import settings
from locales import get_text, LANGUAGES
from database import DatabaseOperations
from services import SubscriptionService

logger = logging.getLogger(__name__)


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /start command - Welcome message and user registration."""
    user = update.effective_user
    db_ops: DatabaseOperations = context.bot_data["db_ops"]
    
    # Create or update user
    await db_ops.create_user(
        user_id=user.id,
        username=user.username,
        first_name=user.first_name,
        last_name=user.last_name,
        language_code=user.language_code or "en"
    )
    
    # Get user's language
    user_data = await db_ops.get_user(user.id)
    lang = user_data.get("language_code", "en") if user_data else "en"
    
    # Send welcome message with keyboard
    keyboard = [
        [InlineKeyboardButton("💬 Start Chatting", callback_data="start_chat")],
        [
            InlineKeyboardButton("⚙️ Settings", callback_data="settings"),
            InlineKeyboardButton("💎 Premium", callback_data="subscribe")
        ],
        [InlineKeyboardButton("🎁 Redeem Code", callback_data="redeem_menu")],
        [InlineKeyboardButton("❓ Help", callback_data="help")]
    ]

    # Add admin panel button for admin user only
    if user.id == settings.admin_user_id:
        keyboard.append([InlineKeyboardButton("🔐 Admin Panel", callback_data="admin_panel")])

    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        get_text("welcome", lang),
        reply_markup=reply_markup
    )
    logger.info(f"User {user.id} started the bot")


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /help command - Display available commands."""
    db_ops: DatabaseOperations = context.bot_data["db_ops"]
    user = update.effective_user
    
    user_data = await db_ops.get_user(user.id)
    lang = user_data.get("language_code", "en") if user_data else "en"
    
    await update.message.reply_text(
        get_text("help", lang),
        parse_mode="Markdown"
    )


async def new_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /new or /reset command - Start a new conversation."""
    db_ops: DatabaseOperations = context.bot_data["db_ops"]
    user = update.effective_user
    
    # Clear conversation history
    await db_ops.clear_conversation(user.id)
    
    user_data = await db_ops.get_user(user.id)
    lang = user_data.get("language_code", "en") if user_data else "en"
    
    await update.message.reply_text(get_text("new_conversation", lang))
    logger.info(f"User {user.id} started new conversation")


async def history_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /history command - View recent conversation history."""
    db_ops: DatabaseOperations = context.bot_data["db_ops"]
    user = update.effective_user
    
    user_data = await db_ops.get_user(user.id)
    lang = user_data.get("language_code", "en") if user_data else "en"
    
    history = await db_ops.get_conversation_history(user.id, limit=10)
    
    if not history:
        await update.message.reply_text(get_text("no_history", lang))
        return
    
    text = get_text("history_header", lang)
    for msg in history[-10:]:
        role = "👤 You" if msg["role"] == "user" else "🤖 AI"
        content = msg["content"][:100] + "..." if len(msg["content"]) > 100 else msg["content"]
        text += f"{role}: {content}\n\n"
    
    await update.message.reply_text(text[:4000])


async def settings_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /settings command - Display and manage user settings."""
    db_ops: DatabaseOperations = context.bot_data["db_ops"]
    sub_service: SubscriptionService = context.bot_data["sub_service"]
    user = update.effective_user
    
    user_data = await db_ops.get_user(user.id)
    if not user_data:
        await update.message.reply_text("Please use /start first.")
        return
    
    lang = user_data.get("language_code", "en")
    model = user_data.get("preferred_model", "gpt-4o-mini")
    sub_info = await sub_service.get_subscription_info(user.id)
    
    text = get_text("settings_menu", lang,
        model=model,
        language=LANGUAGES.get(lang, lang),
        subscription=sub_info["tier_name"]
    )
    
    keyboard = [
        [InlineKeyboardButton("🤖 Change Model", callback_data="select_model")],
        [InlineKeyboardButton("🌐 Change Language", callback_data="select_language")],
        [InlineKeyboardButton("💎 Subscription", callback_data="subscribe")],
        [InlineKeyboardButton("🔙 Back", callback_data="start_chat")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(text, reply_markup=reply_markup, parse_mode="Markdown")


async def subscribe_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /subscribe command - View subscription plans."""
    db_ops: DatabaseOperations = context.bot_data["db_ops"]
    sub_service: SubscriptionService = context.bot_data["sub_service"]
    user = update.effective_user

    user_data = await db_ops.get_user(user.id)
    lang = user_data.get("language_code", "en") if user_data else "en"

    sub_info = await sub_service.get_subscription_info(user.id)
    options = sub_service.get_subscription_options()

    text = get_text("subscribe_info", lang)

    if sub_info["is_premium"]:
        text += f"\n\n{get_text('premium_active', lang, date=sub_info.get('expires_at', 'N/A')[:10])}"

    keyboard = []
    for opt in options:
        keyboard.append([InlineKeyboardButton(
            f"⭐ {opt['name']} - {opt['price_stars']} Stars",
            callback_data=f"buy_{opt['tier']}"
        )])
    keyboard.append([InlineKeyboardButton("🔙 Back", callback_data="settings")])

    await update.message.reply_text(
        text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )


async def generate_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /generate command - Show AI generation options (Premium feature)."""
    db_ops: DatabaseOperations = context.bot_data["db_ops"]
    sub_service: SubscriptionService = context.bot_data["sub_service"]
    user = update.effective_user

    user_data = await db_ops.get_user(user.id)
    lang = user_data.get("language_code", "en") if user_data else "en"

    # Check premium status
    sub_info = await sub_service.get_subscription_info(user.id)

    text = get_text("generate_menu", lang)

    keyboard = [
        [InlineKeyboardButton("🖼️ " + get_text("generate_image_btn", lang), callback_data="gen_image")],
        [InlineKeyboardButton("🎬 " + get_text("generate_video_btn", lang), callback_data="gen_video")],
    ]

    if not sub_info["is_premium"]:
        text += "\n\n" + get_text("generate_premium_required", lang)
        keyboard.append([InlineKeyboardButton("💎 " + get_text("upgrade_premium_btn", lang), callback_data="subscribe")])

    keyboard.append([InlineKeyboardButton("🔙 " + get_text("back_btn", lang), callback_data="start_chat")])

    await update.message.reply_text(
        text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )
    logger.info(f"User {user.id} opened generate menu")


async def redeem_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /redeem command - Redeem a code for premium or credits."""
    db_ops: DatabaseOperations = context.bot_data["db_ops"]
    user = update.effective_user

    user_data = await db_ops.get_user(user.id)
    lang = user_data.get("language_code", "en") if user_data else "en"

    if not context.args:
        keyboard = [[InlineKeyboardButton("🔙 " + get_text("back_btn", lang), callback_data="main_menu")]]
        await update.message.reply_text(
            get_text("redeem_enter_code", lang),
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )
        return

    code = context.args[0].upper()

    # Validate code
    code_data = await db_ops.get_redeem_code(code)

    if not code_data:
        await update.message.reply_text(get_text("redeem_invalid", lang))
        return

    if code_data['is_used']:
        await update.message.reply_text(get_text("redeem_already_used", lang))
        return

    if code_data['is_revoked']:
        await update.message.reply_text(get_text("redeem_invalid", lang))
        return

    # Check expiry
    if code_data['expires_at']:
        expiry = datetime.fromisoformat(code_data['expires_at'])
        if datetime.now() > expiry:
            await update.message.reply_text(get_text("redeem_expired", lang))
            return

    # Apply benefit
    code_type = code_data['code_type']

    if code_type in ['premium_monthly', 'premium_yearly']:
        duration_days = code_data['duration_days']
        await db_ops.grant_premium(user.id, duration_days)
        await db_ops.use_redeem_code(code, user.id)

        await update.message.reply_text(
            get_text("redeem_success_premium", lang, days=duration_days),
            parse_mode="Markdown"
        )
        logger.info(f"User {user.id} redeemed premium code {code} for {duration_days} days")

    elif code_type == 'credits':
        credits = code_data['credits']
        await db_ops.add_user_credits(user.id, credits)
        await db_ops.use_redeem_code(code, user.id)

        await update.message.reply_text(
            get_text("redeem_success_credits", lang, credits=credits),
            parse_mode="Markdown"
        )
        logger.info(f"User {user.id} redeemed credits code {code} for {credits} credits")


def setup_command_handlers(app) -> None:
    """Register all command handlers."""
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler(["new", "reset"], new_command))
    app.add_handler(CommandHandler("history", history_command))
    app.add_handler(CommandHandler("settings", settings_command))
    app.add_handler(CommandHandler("subscribe", subscribe_command))
    app.add_handler(CommandHandler("generate", generate_command))
    app.add_handler(CommandHandler("redeem", redeem_command))

