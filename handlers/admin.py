"""
Admin command handlers restricted to admin user ID.
"""

import logging
import json
from datetime import datetime
from functools import wraps
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CommandHandler

from config import settings
from database import DatabaseOperations
from utils.helpers import format_number, format_timestamp, parse_user_id

logger = logging.getLogger(__name__)


def admin_only(func):
    """Decorator to restrict commands to admin users."""
    @wraps(func)
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
        user_id = update.effective_user.id
        if user_id != settings.admin_user_id:
            await update.message.reply_text("🚫 This command is restricted to administrators.")
            logger.warning(f"Unauthorized admin access attempt by user {user_id}")
            return
        return await func(update, context, *args, **kwargs)
    return wrapper


@admin_only
async def admin_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Admin panel with quick access to admin functions."""
    keyboard = [
        [InlineKeyboardButton("📊 Statistics", callback_data="admin_stats")],
        [InlineKeyboardButton("👥 Users", callback_data="admin_users")],
        [InlineKeyboardButton("📢 Broadcast", callback_data="admin_broadcast")],
        [InlineKeyboardButton("📋 Logs", callback_data="admin_logs")],
        [InlineKeyboardButton("⚙️ Config", callback_data="admin_config")],
        [InlineKeyboardButton("💾 Backup", callback_data="admin_backup")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        "🔐 **Admin Panel**\n\nSelect an option:",
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )


@admin_only
async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """View comprehensive bot statistics."""
    db_ops: DatabaseOperations = context.bot_data["db_ops"]
    
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
• OpenAI requests: {format_number(today_stats.get('openai_requests', 0))}
• Gemini requests: {format_number(today_stats.get('gemini_requests', 0))}
• Tokens used: {format_number(today_stats.get('total_tokens', 0))}

📈 **All Time:**
• Total messages: {format_number(all_time.get('total_messages', 0) or 0)}
• Total tokens: {format_number(all_time.get('total_tokens', 0) or 0)}

💰 **Revenue:**
• Today: {format_number(today_stats.get('total_revenue_stars', 0))} ⭐
• All time: {format_number(all_time.get('total_revenue', 0) or 0)} ⭐

📅 Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}"""

    await update.message.reply_text(text, parse_mode="Markdown")


@admin_only
async def users_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """List and search users."""
    db_ops: DatabaseOperations = context.bot_data["db_ops"]
    args = context.args
    
    if args:
        # Search for specific user
        query = " ".join(args)
        user_id = parse_user_id(query)
        
        if user_id:
            user = await db_ops.get_user(user_id)
            if user:
                text = f"""👤 **User Details**

ID: `{user['user_id']}`
Username: @{user.get('username', 'N/A')}
Name: {user.get('first_name', '')} {user.get('last_name', '')}
Language: {user.get('language_code', 'en')}
Model: {user.get('preferred_model', 'gpt-4o-mini')}
Premium: {'✅' if user.get('is_premium') else '❌'}
Banned: {'🚫' if user.get('is_banned') else '❌'}
Messages: {format_number(user.get('message_count', 0))}
Tokens: {format_number(user.get('total_tokens_used', 0))}
Joined: {format_timestamp(user.get('created_at'))}
Last active: {format_timestamp(user.get('last_active'))}"""
                await update.message.reply_text(text, parse_mode="Markdown")
                return
        
        # Search by username/name
        users = await db_ops.search_users(query)
        if users:
            text = f"🔍 **Search Results for '{query}':**\n\n"
            for u in users[:10]:
                text += f"• `{u['user_id']}` - @{u.get('username', 'N/A')} ({u.get('first_name', 'N/A')})\n"
            await update.message.reply_text(text, parse_mode="Markdown")
        else:
            await update.message.reply_text(f"No users found for '{query}'")
        return
    
    # List recent users
    users = await db_ops.get_all_users(limit=20)
    text = "👥 **Recent Users:**\n\n"
    for u in users:
        premium = "💎" if u.get('is_premium') else ""
        banned = "🚫" if u.get('is_banned') else ""
        text += f"• `{u['user_id']}` - @{u.get('username', 'N/A')} {premium}{banned}\n"
    
    text += "\n💡 Use `/users <id or username>` to see details"
    await update.message.reply_text(text, parse_mode="Markdown")


@admin_only
async def ban_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Ban a user from using the bot."""
    db_ops: DatabaseOperations = context.bot_data["db_ops"]

    if not context.args:
        await update.message.reply_text("Usage: /ban <user_id>")
        return

    user_id = parse_user_id(context.args[0])
    if not user_id:
        await update.message.reply_text("Invalid user ID")
        return

    await db_ops.ban_user(user_id)
    await update.message.reply_text(f"🚫 User {user_id} has been banned.")
    logger.info(f"Admin banned user {user_id}")


@admin_only
async def unban_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Unban a user."""
    db_ops: DatabaseOperations = context.bot_data["db_ops"]

    if not context.args:
        await update.message.reply_text("Usage: /unban <user_id>")
        return

    user_id = parse_user_id(context.args[0])
    if not user_id:
        await update.message.reply_text("Invalid user ID")
        return

    await db_ops.unban_user(user_id)
    await update.message.reply_text(f"✅ User {user_id} has been unbanned.")
    logger.info(f"Admin unbanned user {user_id}")


@admin_only
async def grant_premium_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Manually grant premium to a user."""
    db_ops: DatabaseOperations = context.bot_data["db_ops"]

    if len(context.args) < 1:
        await update.message.reply_text("Usage: /grant_premium <user_id> [days=30]")
        return

    user_id = parse_user_id(context.args[0])
    days = int(context.args[1]) if len(context.args) > 1 else 30

    if not user_id:
        await update.message.reply_text("Invalid user ID")
        return

    await db_ops.grant_premium(user_id, days)
    await update.message.reply_text(f"✅ Premium granted to user {user_id} for {days} days.")
    logger.info(f"Admin granted premium to user {user_id} for {days} days")


@admin_only
async def revoke_premium_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Revoke premium from a user."""
    db_ops: DatabaseOperations = context.bot_data["db_ops"]

    if not context.args:
        await update.message.reply_text("Usage: /revoke_premium <user_id>")
        return

    user_id = parse_user_id(context.args[0])
    if not user_id:
        await update.message.reply_text("Invalid user ID")
        return

    await db_ops.revoke_premium(user_id)
    await update.message.reply_text(f"✅ Premium revoked from user {user_id}.")
    logger.info(f"Admin revoked premium from user {user_id}")


@admin_only
async def broadcast_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Broadcast a message to all users."""
    db_ops: DatabaseOperations = context.bot_data["db_ops"]

    if not context.args:
        await update.message.reply_text(
            "📢 **Broadcast Message**\n\n"
            "Usage: /broadcast <message>\n\n"
            "Options:\n"
            "• `/broadcast all <message>` - Send to all users\n"
            "• `/broadcast premium <message>` - Send to premium users only",
            parse_mode="Markdown"
        )
        return

    target = context.args[0].lower()
    if target in ["all", "premium"]:
        message = " ".join(context.args[1:])
        if target == "premium":
            users = await db_ops.get_premium_users()
        else:
            users = await db_ops.get_all_users(limit=10000)
    else:
        message = " ".join(context.args)
        users = await db_ops.get_all_users(limit=10000)

    if not message:
        await update.message.reply_text("Please provide a message to broadcast.")
        return

    # Send broadcast
    sent = 0
    failed = 0
    status_msg = await update.message.reply_text("📤 Broadcasting...")

    for user in users:
        try:
            await context.bot.send_message(
                chat_id=user["user_id"],
                text=f"📢 **Announcement**\n\n{message}",
                parse_mode="Markdown"
            )
            sent += 1
        except Exception as e:
            failed += 1
            logger.debug(f"Failed to send broadcast to {user['user_id']}: {e}")

    await status_msg.edit_text(f"✅ Broadcast complete!\nSent: {sent}, Failed: {failed}")
    logger.info(f"Admin broadcast: sent={sent}, failed={failed}")


@admin_only
async def logs_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """View recent error logs."""
    db_ops: DatabaseOperations = context.bot_data["db_ops"]

    errors = await db_ops.get_recent_errors(limit=20)

    if not errors:
        await update.message.reply_text("No recent errors logged.")
        return

    text = "📋 **Recent Errors:**\n\n"
    for err in errors[:10]:
        text += f"• [{format_timestamp(err.get('created_at'))}] {err.get('error_type', 'unknown')}\n"
        text += f"  {err.get('error_message', '')[:100]}\n\n"

    await update.message.reply_text(text, parse_mode="Markdown")


@admin_only
async def backup_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Export database backup."""
    db_ops: DatabaseOperations = context.bot_data["db_ops"]

    await update.message.reply_text("📦 Generating backup...")

    try:
        data = await db_ops.export_data()
        backup_json = json.dumps(data, indent=2, default=str)

        # Send as document
        import io
        file = io.BytesIO(backup_json.encode('utf-8'))
        file.name = f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

        await update.message.reply_document(
            document=file,
            caption="✅ Database backup generated successfully."
        )
        logger.info("Admin generated database backup")
    except Exception as e:
        await update.message.reply_text(f"❌ Backup failed: {e}")
        logger.error(f"Backup error: {e}")


@admin_only
async def config_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """View and update bot configuration."""
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
• OpenAI: {'✅' if settings.openai_api_key else '❌'}
• Gemini: {'✅' if settings.gemini_api_key else '❌'}

💡 Config changes require .env file modification and bot restart."""

    await update.message.reply_text(text, parse_mode="Markdown")


def setup_admin_handlers(app) -> None:
    """Register admin command handlers."""
    app.add_handler(CommandHandler("admin", admin_command))
    app.add_handler(CommandHandler("stats", stats_command))
    app.add_handler(CommandHandler("users", users_command))
    app.add_handler(CommandHandler("ban", ban_command))
    app.add_handler(CommandHandler("unban", unban_command))
    app.add_handler(CommandHandler("grant_premium", grant_premium_command))
    app.add_handler(CommandHandler("revoke_premium", revoke_premium_command))
    app.add_handler(CommandHandler("broadcast", broadcast_command))
    app.add_handler(CommandHandler("logs", logs_command))
    app.add_handler(CommandHandler("backup", backup_command))
    app.add_handler(CommandHandler("config", config_command))
