"""
Payment handlers for Telegram Stars subscriptions.
"""

import logging
from telegram import Update, LabeledPrice
from telegram.ext import ContextTypes, PreCheckoutQueryHandler, MessageHandler, filters

from config import settings
from database import DatabaseOperations
from services import SubscriptionService
from services.subscription_service import SubscriptionTier

logger = logging.getLogger(__name__)


async def send_invoice(update: Update, context: ContextTypes.DEFAULT_TYPE, tier: str) -> None:
    """Send a Telegram Stars invoice for subscription."""
    sub_service: SubscriptionService = context.bot_data["sub_service"]
    
    tier_enum = SubscriptionTier.MONTHLY if tier == "monthly" else SubscriptionTier.YEARLY
    tier_info = sub_service.TIERS[tier_enum]
    
    title = f"Premium {tier.capitalize()} Subscription"
    description = f"AI Assistant Premium - {tier_info['duration_days']} days\n\n" + \
                  "\n".join(f"✓ {f}" for f in tier_info["features"])
    
    prices = [LabeledPrice(label=title, amount=tier_info["price_stars"])]
    
    await update.effective_chat.send_invoice(
        title=title,
        description=description,
        payload=f"subscription_{tier}",
        provider_token="",  # Empty for Telegram Stars
        currency="XTR",  # Telegram Stars currency
        prices=prices,
    )


async def pre_checkout_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle pre-checkout queries to validate payment."""
    query = update.pre_checkout_query
    
    # Validate the payment
    if query.invoice_payload.startswith("subscription_"):
        await query.answer(ok=True)
        logger.info(f"Pre-checkout approved for user {query.from_user.id}: {query.invoice_payload}")
    else:
        await query.answer(ok=False, error_message="Invalid payment type")


async def successful_payment_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle successful payment and activate subscription."""
    message = update.message
    payment = message.successful_payment
    user = update.effective_user
    
    db_ops: DatabaseOperations = context.bot_data["db_ops"]
    sub_service: SubscriptionService = context.bot_data["sub_service"]
    
    try:
        # Parse payment info
        payload = payment.invoice_payload
        tier_str = payload.replace("subscription_", "")
        tier = SubscriptionTier.MONTHLY if tier_str == "monthly" else SubscriptionTier.YEARLY
        
        # Process the subscription
        result = await sub_service.process_subscription_payment(
            user_id=user.id,
            tier=tier,
            telegram_payment_id=payment.telegram_payment_charge_id
        )
        
        if result["success"]:
            await message.reply_text(
                f"🎉 **Thank you for subscribing!**\n\n"
                f"✅ Your Premium subscription is now active!\n"
                f"📅 Valid for {result['expires_in_days']} days\n\n"
                f"Enjoy unlimited AI access, all models, voice messages, and image analysis!",
                parse_mode="Markdown"
            )
            logger.info(f"User {user.id} subscribed: {tier.value}, payment: {payment.telegram_payment_charge_id}")
        else:
            await message.reply_text(
                "❌ There was an issue processing your subscription. Please contact support."
            )
            
    except Exception as e:
        logger.error(f"Payment processing error: {e}")
        await message.reply_text(
            "❌ Payment received but subscription activation failed. Please contact support."
        )
        await db_ops.log_error("payment_processing", str(e), user_id=user.id)


def setup_payment_handlers(app) -> None:
    """Register payment handlers."""
    app.add_handler(PreCheckoutQueryHandler(pre_checkout_handler))
    app.add_handler(MessageHandler(filters.SUCCESSFUL_PAYMENT, successful_payment_handler))

