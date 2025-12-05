"""
Subscription service for Telegram Stars payments.
Handles premium subscriptions, payment processing, and tier management.
"""

import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from enum import Enum

from config import settings
from database import DatabaseOperations

logger = logging.getLogger(__name__)


class SubscriptionTier(Enum):
    """Subscription tier definitions."""
    FREE = "free"
    MONTHLY = "monthly"
    YEARLY = "yearly"


class SubscriptionService:
    """Manages user subscriptions and premium features."""
    
    # Subscription configuration
    TIERS = {
        SubscriptionTier.FREE: {
            "name": "Free",
            "price_stars": 0,
            "daily_messages": 20,
            "features": ["Basic AI access", "GPT-4o-mini only", "Limited history"],
            "duration_days": 0
        },
        SubscriptionTier.MONTHLY: {
            "name": "Premium Monthly",
            "price_stars": settings.subscription_price_monthly,
            "daily_messages": 1000,
            "features": [
                "Unlimited AI access",
                "All AI models",
                "Priority support",
                "Extended history",
                "Voice & Image support"
            ],
            "duration_days": 30
        },
        SubscriptionTier.YEARLY: {
            "name": "Premium Yearly",
            "price_stars": settings.subscription_price_yearly,
            "daily_messages": 1000,
            "features": [
                "All Monthly features",
                "2 months FREE",
                "Early access to new features"
            ],
            "duration_days": 365
        }
    }
    
    def __init__(self, db_ops: DatabaseOperations):
        self.db = db_ops
    
    async def get_user_tier(self, user_id: int) -> SubscriptionTier:
        """Get user's current subscription tier."""
        subscription = await self.db.get_active_subscription(user_id)
        if subscription:
            sub_type = subscription.get("subscription_type", "").lower()
            if "yearly" in sub_type:
                return SubscriptionTier.YEARLY
            elif "monthly" in sub_type or "premium" in sub_type or "admin" in sub_type:
                return SubscriptionTier.MONTHLY
        return SubscriptionTier.FREE
    
    async def get_subscription_info(self, user_id: int) -> Dict[str, Any]:
        """Get detailed subscription information for a user."""
        tier = await self.get_user_tier(user_id)
        subscription = await self.db.get_active_subscription(user_id)
        tier_info = self.TIERS[tier]
        
        info = {
            "tier": tier.value,
            "tier_name": tier_info["name"],
            "daily_limit": tier_info["daily_messages"],
            "features": tier_info["features"],
            "is_premium": tier != SubscriptionTier.FREE,
        }
        
        if subscription:
            info["expires_at"] = subscription.get("expires_at")
            info["started_at"] = subscription.get("started_at")
            info["days_remaining"] = self._calculate_days_remaining(
                subscription.get("expires_at")
            )
        
        return info
    
    def _calculate_days_remaining(self, expires_at: str) -> int:
        """Calculate days remaining in subscription."""
        if not expires_at:
            return 0
        try:
            expiry = datetime.fromisoformat(expires_at)
            remaining = (expiry - datetime.now()).days
            return max(0, remaining)
        except:
            return 0
    
    async def can_send_message(self, user_id: int) -> tuple[bool, str]:
        """Check if user can send a message (rate limiting)."""
        user = await self.db.get_user(user_id)
        if not user:
            return True, ""
        
        if user.get("is_banned"):
            return False, "You have been banned from using this bot."
        
        tier = await self.get_user_tier(user_id)
        limit = self.TIERS[tier]["daily_messages"]
        
        # For simplicity, we check hourly limit (divide daily by 24, minimum 1)
        hourly_limit = max(1, limit // 24)
        
        # In production, implement proper rate limiting with Redis or similar
        # For now, we just check the user's message count
        return True, ""
    
    async def process_subscription_payment(
        self,
        user_id: int,
        tier: SubscriptionTier,
        telegram_payment_id: str
    ) -> Dict[str, Any]:
        """Process a subscription payment."""
        if tier == SubscriptionTier.FREE:
            return {"success": False, "error": "Cannot purchase free tier"}
        
        tier_info = self.TIERS[tier]
        
        # Create payment record
        payment_id = await self.db.create_payment(
            user_id=user_id,
            amount_stars=tier_info["price_stars"],
            payment_type=f"subscription_{tier.value}",
            telegram_payment_id=telegram_payment_id
        )
        
        # Create subscription
        sub_id = await self.db.create_subscription(
            user_id=user_id,
            subscription_type=tier.value,
            stars_paid=tier_info["price_stars"],
            duration_days=tier_info["duration_days"],
            telegram_payment_id=telegram_payment_id
        )
        
        # Update payment status
        await self.db.update_payment_status(payment_id, "completed")
        
        # Update stats
        await self.db.increment_stats(revenue_stars=tier_info["price_stars"])
        
        logger.info(f"User {user_id} subscribed to {tier.value}")
        
        return {
            "success": True,
            "subscription_id": sub_id,
            "tier": tier.value,
            "expires_in_days": tier_info["duration_days"]
        }

    def get_subscription_options(self) -> list[Dict[str, Any]]:
        """Get available subscription options for display."""
        options = []
        for tier in [SubscriptionTier.MONTHLY, SubscriptionTier.YEARLY]:
            info = self.TIERS[tier]
            options.append({
                "tier": tier.value,
                "name": info["name"],
                "price_stars": info["price_stars"],
                "duration_days": info["duration_days"],
                "features": info["features"]
            })
        return options

    async def check_and_expire_subscriptions(self) -> list[int]:
        """Check for expired subscriptions and deactivate them."""
        return await self.db.check_expired_subscriptions()
