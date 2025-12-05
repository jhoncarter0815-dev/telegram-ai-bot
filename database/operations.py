"""
Database operations for user management, subscriptions, and statistics.
"""

from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
import logging

from .models import Database

logger = logging.getLogger(__name__)


class DatabaseOperations:
    """High-level database operations."""
    
    def __init__(self, db: Database):
        self.db = db
    
    # ==================== User Operations ====================
    
    async def get_user(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Get user by ID."""
        row = await self.db.fetch_one(
            "SELECT * FROM users WHERE user_id = ?", (user_id,)
        )
        return dict(row) if row else None
    
    async def create_user(
        self,
        user_id: int,
        username: str = None,
        first_name: str = None,
        last_name: str = None,
        language_code: str = "en"
    ) -> Dict[str, Any]:
        """Create a new user or update existing."""
        existing = await self.get_user(user_id)
        if existing:
            await self.db.execute(
                """UPDATE users SET username = ?, first_name = ?, last_name = ?, 
                   last_active = CURRENT_TIMESTAMP WHERE user_id = ?""",
                (username, first_name, last_name, user_id)
            )
        else:
            await self.db.execute(
                """INSERT INTO users (user_id, username, first_name, last_name, language_code)
                   VALUES (?, ?, ?, ?, ?)""",
                (user_id, username, first_name, last_name, language_code)
            )
            await self._increment_new_users()
        return await self.get_user(user_id)
    
    async def update_user_preference(self, user_id: int, key: str, value: Any) -> None:
        """Update a user preference."""
        valid_keys = ["language_code", "preferred_model", "is_premium", "is_banned"]
        if key not in valid_keys:
            raise ValueError(f"Invalid preference key: {key}")
        await self.db.execute(
            f"UPDATE users SET {key} = ? WHERE user_id = ?", (value, user_id)
        )
    
    async def increment_message_count(self, user_id: int, tokens: int = 0) -> None:
        """Increment user's message count and tokens used."""
        await self.db.execute(
            """UPDATE users SET message_count = message_count + 1, 
               total_tokens_used = total_tokens_used + ?,
               last_active = CURRENT_TIMESTAMP WHERE user_id = ?""",
            (tokens, user_id)
        )
    
    async def get_all_users(self, limit: int = 100, offset: int = 0) -> List[Dict]:
        """Get all users with pagination."""
        rows = await self.db.fetch_all(
            "SELECT * FROM users ORDER BY last_active DESC LIMIT ? OFFSET ?",
            (limit, offset)
        )
        return [dict(row) for row in rows]
    
    async def search_users(self, query: str) -> List[Dict]:
        """Search users by username or name."""
        rows = await self.db.fetch_all(
            """SELECT * FROM users WHERE 
               username LIKE ? OR first_name LIKE ? OR last_name LIKE ?
               ORDER BY last_active DESC LIMIT 50""",
            (f"%{query}%", f"%{query}%", f"%{query}%")
        )
        return [dict(row) for row in rows]
    
    async def ban_user(self, user_id: int) -> None:
        """Ban a user."""
        await self.db.execute(
            "UPDATE users SET is_banned = 1 WHERE user_id = ?", (user_id,)
        )
    
    async def unban_user(self, user_id: int) -> None:
        """Unban a user."""
        await self.db.execute(
            "UPDATE users SET is_banned = 0 WHERE user_id = ?", (user_id,)
        )
    
    async def is_user_banned(self, user_id: int) -> bool:
        """Check if user is banned."""
        row = await self.db.fetch_one(
            "SELECT is_banned FROM users WHERE user_id = ?", (user_id,)
        )
        return bool(row["is_banned"]) if row else False
    
    async def get_user_count(self) -> int:
        """Get total number of users."""
        row = await self.db.fetch_one("SELECT COUNT(*) as count FROM users")
        return row["count"] if row else 0
    
    async def get_active_users_count(self, hours: int = 24) -> int:
        """Get count of users active in the last N hours."""
        threshold = datetime.now() - timedelta(hours=hours)
        row = await self.db.fetch_one(
            "SELECT COUNT(*) as count FROM users WHERE last_active > ?",
            (threshold.isoformat(),)
        )
        return row["count"] if row else 0
    
    async def get_premium_users(self) -> List[Dict]:
        """Get all premium users."""
        rows = await self.db.fetch_all(
            "SELECT * FROM users WHERE is_premium = 1"
        )
        return [dict(row) for row in rows]

    # ==================== Subscription Operations ====================

    async def create_subscription(
        self,
        user_id: int,
        subscription_type: str,
        stars_paid: int,
        duration_days: int,
        telegram_payment_id: str = None
    ) -> int:
        """Create a new subscription."""
        expires_at = datetime.now() + timedelta(days=duration_days)
        cursor = await self.db.execute(
            """INSERT INTO subscriptions
               (user_id, subscription_type, stars_paid, expires_at, telegram_payment_id)
               VALUES (?, ?, ?, ?, ?)""",
            (user_id, subscription_type, stars_paid, expires_at.isoformat(), telegram_payment_id)
        )
        await self.update_user_preference(user_id, "is_premium", 1)
        return cursor.lastrowid

    async def get_active_subscription(self, user_id: int) -> Optional[Dict]:
        """Get user's active subscription."""
        row = await self.db.fetch_one(
            """SELECT * FROM subscriptions
               WHERE user_id = ? AND is_active = 1 AND expires_at > datetime('now')
               ORDER BY expires_at DESC LIMIT 1""",
            (user_id,)
        )
        return dict(row) if row else None

    async def deactivate_subscription(self, subscription_id: int) -> None:
        """Deactivate a subscription."""
        await self.db.execute(
            "UPDATE subscriptions SET is_active = 0 WHERE id = ?",
            (subscription_id,)
        )

    async def check_expired_subscriptions(self) -> List[int]:
        """Check and deactivate expired subscriptions, return affected user IDs."""
        rows = await self.db.fetch_all(
            """SELECT user_id, id FROM subscriptions
               WHERE is_active = 1 AND expires_at <= datetime('now')"""
        )
        affected_users = []
        for row in rows:
            await self.deactivate_subscription(row["id"])
            await self.update_user_preference(row["user_id"], "is_premium", 0)
            affected_users.append(row["user_id"])
        return affected_users

    async def grant_premium(self, user_id: int, days: int = 30) -> None:
        """Manually grant premium to a user."""
        await self.create_subscription(user_id, "admin_grant", 0, days)

    async def revoke_premium(self, user_id: int) -> None:
        """Revoke premium from a user."""
        await self.db.execute(
            "UPDATE subscriptions SET is_active = 0 WHERE user_id = ?",
            (user_id,)
        )
        await self.update_user_preference(user_id, "is_premium", 0)

    # ==================== Conversation Operations ====================

    async def add_message(
        self,
        user_id: int,
        role: str,
        content: str,
        model_used: str = None,
        tokens_used: int = 0
    ) -> int:
        """Add a message to conversation history."""
        cursor = await self.db.execute(
            """INSERT INTO conversations (user_id, role, content, model_used, tokens_used)
               VALUES (?, ?, ?, ?, ?)""",
            (user_id, role, content, model_used, tokens_used)
        )
        return cursor.lastrowid

    async def get_conversation_history(
        self,
        user_id: int,
        limit: int = 20
    ) -> List[Dict]:
        """Get recent conversation history for a user."""
        rows = await self.db.fetch_all(
            """SELECT role, content, created_at FROM conversations
               WHERE user_id = ? ORDER BY created_at DESC LIMIT ?""",
            (user_id, limit)
        )
        return [dict(row) for row in reversed(rows)]

    async def clear_conversation(self, user_id: int) -> None:
        """Clear conversation history for a user."""
        await self.db.execute(
            "DELETE FROM conversations WHERE user_id = ?", (user_id,)
        )

    # ==================== Statistics Operations ====================

    async def _ensure_today_stats(self) -> None:
        """Ensure today's stats row exists."""
        await self.db.execute(
            """INSERT OR IGNORE INTO bot_stats (stat_date) VALUES (date('now'))"""
        )

    async def _increment_new_users(self) -> None:
        """Increment new users count for today."""
        await self._ensure_today_stats()
        await self.db.execute(
            """UPDATE bot_stats SET new_users = new_users + 1,
               total_users = (SELECT COUNT(*) FROM users)
               WHERE stat_date = date('now')"""
        )

    async def increment_stats(
        self,
        messages: int = 0,
        openai_requests: int = 0,
        gemini_requests: int = 0,
        tokens: int = 0,
        revenue_stars: int = 0
    ) -> None:
        """Increment various stats for today."""
        await self._ensure_today_stats()
        await self.db.execute(
            """UPDATE bot_stats SET
               total_messages = total_messages + ?,
               openai_requests = openai_requests + ?,
               gemini_requests = gemini_requests + ?,
               total_tokens = total_tokens + ?,
               total_revenue_stars = total_revenue_stars + ?
               WHERE stat_date = date('now')""",
            (messages, openai_requests, gemini_requests, tokens, revenue_stars)
        )

    async def get_today_stats(self) -> Dict:
        """Get today's statistics."""
        await self._ensure_today_stats()
        row = await self.db.fetch_one(
            "SELECT * FROM bot_stats WHERE stat_date = date('now')"
        )
        return dict(row) if row else {}

    async def get_all_time_stats(self) -> Dict:
        """Get all-time statistics."""
        row = await self.db.fetch_one(
            """SELECT
               SUM(total_messages) as total_messages,
               SUM(openai_requests) as openai_requests,
               SUM(gemini_requests) as gemini_requests,
               SUM(total_tokens) as total_tokens,
               SUM(total_revenue_stars) as total_revenue
               FROM bot_stats"""
        )
        user_count = await self.get_user_count()
        result = dict(row) if row else {}
        result["total_users"] = user_count
        return result

    # ==================== Error Logging ====================

    async def log_error(
        self,
        error_type: str,
        error_message: str,
        stack_trace: str = None,
        user_id: int = None
    ) -> None:
        """Log an error to the database."""
        await self.db.execute(
            """INSERT INTO error_logs (user_id, error_type, error_message, stack_trace)
               VALUES (?, ?, ?, ?)""",
            (user_id, error_type, error_message, stack_trace)
        )

    async def get_recent_errors(self, limit: int = 50) -> List[Dict]:
        """Get recent error logs."""
        rows = await self.db.fetch_all(
            "SELECT * FROM error_logs ORDER BY created_at DESC LIMIT ?",
            (limit,)
        )
        return [dict(row) for row in rows]

    # ==================== Payment Operations ====================

    async def create_payment(
        self,
        user_id: int,
        amount_stars: int,
        payment_type: str,
        telegram_payment_id: str = None
    ) -> int:
        """Record a payment."""
        cursor = await self.db.execute(
            """INSERT INTO payments (user_id, amount_stars, payment_type, telegram_payment_id)
               VALUES (?, ?, ?, ?)""",
            (user_id, amount_stars, payment_type, telegram_payment_id)
        )
        return cursor.lastrowid

    async def update_payment_status(self, payment_id: int, status: str) -> None:
        """Update payment status."""
        await self.db.execute(
            "UPDATE payments SET status = ? WHERE id = ?",
            (status, payment_id)
        )

    async def get_user_payments(self, user_id: int) -> List[Dict]:
        """Get payment history for a user."""
        rows = await self.db.fetch_all(
            "SELECT * FROM payments WHERE user_id = ? ORDER BY created_at DESC",
            (user_id,)
        )
        return [dict(row) for row in rows]

    async def get_total_revenue(self) -> int:
        """Get total revenue in stars."""
        row = await self.db.fetch_one(
            "SELECT SUM(amount_stars) as total FROM payments WHERE status = 'completed'"
        )
        return row["total"] if row and row["total"] else 0

    # ==================== Backup Operations ====================

    async def export_data(self) -> Dict:
        """Export all data for backup."""
        users = await self.db.fetch_all("SELECT * FROM users")
        subs = await self.db.fetch_all("SELECT * FROM subscriptions")
        stats = await self.db.fetch_all("SELECT * FROM bot_stats")
        payments = await self.db.fetch_all("SELECT * FROM payments")

        return {
            "users": [dict(row) for row in users],
            "subscriptions": [dict(row) for row in subs],
            "bot_stats": [dict(row) for row in stats],
            "payments": [dict(row) for row in payments],
            "exported_at": datetime.now().isoformat()
        }

