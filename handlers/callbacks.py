"""
Callback query handlers for inline keyboard interactions.
"""

import logging
import io
import json
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CallbackQueryHandler, ConversationHandler, MessageHandler, filters

from config import settings
from locales import get_text, LANGUAGES
from database import DatabaseOperations
from services import AIService, SubscriptionService
from utils.helpers import format_number, format_timestamp

logger = logging.getLogger(__name__)

# Conversation states for generation
WAITING_IMAGE_PROMPT = 1
WAITING_VIDEO_PROMPT = 2


async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Main callback handler that routes to specific handlers."""
    query = update.callback_query
    await query.answer()

    data = query.data
    user = update.effective_user

    logger.info(f"Callback received: {data} from user {user.id}")

    try:
        db_ops: DatabaseOperations = context.bot_data["db_ops"]
        sub_service: SubscriptionService = context.bot_data["sub_service"]
        ai_service: AIService = context.bot_data["ai_service"]

        user_data = await db_ops.get_user(user.id)
        lang = user_data.get("language_code", "en") if user_data else "en"

        # Check if user is admin
        is_admin = user.id == settings.admin_user_id
    except Exception as e:
        logger.error(f"Callback init error: {e}")
        await query.edit_message_text(f"❌ Error: {e}")
        return

    # Route callbacks
    if data == "main_menu":
        # Show main menu
        keyboard = [
            [InlineKeyboardButton("💬 Start Chatting", callback_data="start_chat")],
            [
                InlineKeyboardButton("⚙️ Settings", callback_data="settings"),
                InlineKeyboardButton("💎 Premium", callback_data="subscribe")
            ],
            [InlineKeyboardButton("❓ Help", callback_data="help")]
        ]
        if is_admin:
            keyboard.append([InlineKeyboardButton("🔐 Admin Panel", callback_data="admin_panel")])

        await query.edit_message_text(
            get_text("welcome", lang),
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    elif data == "start_chat":
        keyboard = [[InlineKeyboardButton("🔙 Back to Menu", callback_data="main_menu")]]
        await query.edit_message_text(
            "💬 Just send me a message to start chatting!\n\n"
            "You can send:\n"
            "• Text messages\n"
            "• Voice messages (Premium)\n"
            "• Images (Premium)",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    elif data == "help":
        keyboard = [[InlineKeyboardButton("🔙 Back to Menu", callback_data="main_menu")]]
        await query.edit_message_text(
            get_text("help", lang),
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )
    
    elif data == "settings":
        logger.info(f"User {user.id} opened settings")
        model = user_data.get("preferred_model", "gemini-2.0-flash") if user_data else "gemini-2.0-flash"
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
            [InlineKeyboardButton("🔙 Back to Menu", callback_data="main_menu")]
        ]
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")
    
    elif data == "select_model":
        models = ai_service.get_available_models()
        keyboard = []
        for model in models:
            current = "✅ " if model["id"] == user_data.get("preferred_model") else ""
            keyboard.append([InlineKeyboardButton(
                f"{current}{model['name']} ({model['provider']})",
                callback_data=f"model_{model['id']}"
            )])
        keyboard.append([InlineKeyboardButton("🔙 Back", callback_data="settings")])
        
        await query.edit_message_text(
            "🤖 **Select AI Model**\n\nChoose your preferred AI model:",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )
    
    elif data.startswith("model_"):
        model_id = data.replace("model_", "")
        await db_ops.update_user_preference(user.id, "preferred_model", model_id)
        keyboard = [[InlineKeyboardButton("🔙 Back to Settings", callback_data="settings")]]
        await query.edit_message_text(
            get_text("model_changed", lang, model=model_id),
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        logger.info(f"User {user.id} changed model to {model_id}")
    
    elif data == "select_language":
        keyboard = []
        for code, name in LANGUAGES.items():
            current = "✅ " if code == lang else ""
            keyboard.append([InlineKeyboardButton(
                f"{current}{name}",
                callback_data=f"lang_{code}"
            )])
        keyboard.append([InlineKeyboardButton("🔙 Back", callback_data="settings")])
        
        await query.edit_message_text(
            "🌐 **Select Language**",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )
    
    elif data.startswith("lang_"):
        new_lang = data.replace("lang_", "")
        await db_ops.update_user_preference(user.id, "language_code", new_lang)
        keyboard = [[InlineKeyboardButton("🔙 Back to Settings", callback_data="settings")]]
        await query.edit_message_text(
            get_text("language_changed", new_lang),
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        logger.info(f"User {user.id} changed language to {new_lang}")
    
    elif data == "subscribe":
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
        keyboard.append([InlineKeyboardButton("🔙 Back to Menu", callback_data="main_menu")])

        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")
    
    elif data.startswith("buy_"):
        tier = data.replace("buy_", "")
        # Redirect to payment - handled by payment handler
        await query.edit_message_text(
            f"💫 To purchase {tier} subscription, use the payment button below:",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("💳 Pay with Stars", callback_data=f"pay_{tier}")],
                [InlineKeyboardButton("🔙 Back", callback_data="subscribe")]
            ])
        )

    elif data.startswith("pay_"):
        tier = data.replace("pay_", "")
        from handlers.payments import send_invoice
        await query.message.delete()
        await send_invoice(update, context, tier)

    # Admin Panel Callbacks
    elif data == "admin_stats":
        if user.id != settings.admin_user_id:
            await query.edit_message_text("🚫 Unauthorized access.")
            return

        today_stats = await db_ops.get_today_stats()
        all_time = await db_ops.get_all_time_stats()
        active_24h = await db_ops.get_active_users_count(24)
        premium_users = await db_ops.get_premium_users()

        text = f"""📊 **Bot Statistics**

👥 **Users:**
• Total users: {format_number(all_time.get('total_users', 0))}
• Active (24h): {format_number(active_24h)}
• Premium users: {len(premium_users)}

📨 **Messages Today:**
• Messages: {format_number(today_stats.get('total_messages', 0))}
• Gemini requests: {format_number(today_stats.get('gemini_requests', 0))}
• Tokens used: {format_number(today_stats.get('total_tokens', 0))}

📈 **All Time:**
• Total messages: {format_number(all_time.get('total_messages', 0) or 0)}
• Total tokens: {format_number(all_time.get('total_tokens', 0) or 0)}

💰 **Revenue:**
• Today: {format_number(today_stats.get('total_revenue_stars', 0))} ⭐
• All time: {format_number(all_time.get('total_revenue', 0) or 0)} ⭐

📅 Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}"""

        keyboard = [[InlineKeyboardButton("🔙 Back to Admin", callback_data="admin_panel")]]
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")

    elif data == "admin_users":
        if user.id != settings.admin_user_id:
            await query.edit_message_text("🚫 Unauthorized access.")
            return

        users = await db_ops.get_all_users(limit=15)
        text = "👥 **Recent Users:**\n\n"
        for u in users:
            premium = "💎" if u.get('is_premium') else ""
            banned = "🚫" if u.get('is_banned') else ""
            text += f"• `{u['user_id']}` - @{u.get('username', 'N/A')} {premium}{banned}\n"

        text += "\n💡 Use `/users <id or username>` command for details"

        keyboard = [[InlineKeyboardButton("🔙 Back to Admin", callback_data="admin_panel")]]
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")

    elif data == "admin_broadcast":
        if user.id != settings.admin_user_id:
            await query.edit_message_text("🚫 Unauthorized access.")
            return

        text = """📢 **Broadcast Message**

Use the command to send a broadcast:

• `/broadcast <message>` - Send to all users
• `/broadcast all <message>` - Send to all users
• `/broadcast premium <message>` - Send to premium users only

Example:
`/broadcast Hello everyone! New features are coming soon!`"""

        keyboard = [[InlineKeyboardButton("🔙 Back to Admin", callback_data="admin_panel")]]
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")

    elif data == "admin_logs":
        if user.id != settings.admin_user_id:
            await query.edit_message_text("🚫 Unauthorized access.")
            return

        errors = await db_ops.get_recent_errors(limit=10)

        if not errors:
            text = "📋 **Recent Errors:**\n\nNo recent errors logged. ✅"
        else:
            text = "📋 **Recent Errors:**\n\n"
            for err in errors[:5]:
                text += f"• [{format_timestamp(err.get('created_at'))}] {err.get('error_type', 'unknown')}\n"
                text += f"  {err.get('error_message', '')[:80]}\n\n"

        keyboard = [[InlineKeyboardButton("🔙 Back to Admin", callback_data="admin_panel")]]
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")

    elif data == "admin_config":
        if user.id != settings.admin_user_id:
            await query.edit_message_text("🚫 Unauthorized access.")
            return

        text = f"""⚙️ **Current Configuration**

**Rate Limits:**
• Free tier: {settings.free_tier_limit} msgs/hour
• Premium tier: {settings.premium_tier_limit} msgs/hour

**Subscription Prices:**
• Monthly: {settings.subscription_price_monthly} ⭐
• Yearly: {settings.subscription_price_yearly} ⭐

**AI Settings:**
• Default model: {settings.default_ai_model}
• Max context: {settings.max_context_messages} messages

**API Status:**
• Gemini: {'✅' if settings.gemini_api_key else '❌'}

💡 Config changes require .env file modification and bot restart."""

        keyboard = [[InlineKeyboardButton("🔙 Back to Admin", callback_data="admin_panel")]]
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")

    elif data == "admin_backup":
        if user.id != settings.admin_user_id:
            await query.edit_message_text("🚫 Unauthorized access.")
            return

        await query.edit_message_text("📦 Generating backup...")

        try:
            data_export = await db_ops.export_data()
            backup_json = json.dumps(data_export, indent=2, default=str)

            file = io.BytesIO(backup_json.encode('utf-8'))
            file.name = f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

            await query.message.reply_document(
                document=file,
                caption="✅ Database backup generated successfully."
            )

            keyboard = [[InlineKeyboardButton("🔙 Back to Admin", callback_data="admin_panel")]]
            await query.edit_message_text("✅ Backup sent!", reply_markup=InlineKeyboardMarkup(keyboard))
            logger.info("Admin generated database backup via callback")
        except Exception as e:
            await query.edit_message_text(f"❌ Backup failed: {e}")
            logger.error(f"Backup error: {e}")

    elif data == "admin_panel":
        if user.id != settings.admin_user_id:
            await query.edit_message_text("🚫 Unauthorized access.")
            return

        keyboard = [
            [InlineKeyboardButton("📊 Statistics", callback_data="admin_stats")],
            [InlineKeyboardButton("👥 Users", callback_data="admin_users")],
            [InlineKeyboardButton("📢 Broadcast", callback_data="admin_broadcast")],
            [InlineKeyboardButton("📋 Logs", callback_data="admin_logs")],
            [InlineKeyboardButton("⚙️ Config", callback_data="admin_config")],
            [InlineKeyboardButton("💾 Backup", callback_data="admin_backup")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await query.edit_message_text(
            "🔐 **Admin Panel**\n\nSelect an option:",
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )


def setup_callback_handlers(app) -> None:
    """Register callback handlers."""
    app.add_handler(CallbackQueryHandler(handle_callback))
