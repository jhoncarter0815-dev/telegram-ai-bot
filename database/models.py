"""
Database models and schema definitions.
Uses aiosqlite for async SQLite operations.
"""

import aiosqlite
import os
from datetime import datetime
from typing import Optional
import logging

logger = logging.getLogger(__name__)


class Database:
    """Async SQLite database manager."""
    
    def __init__(self, db_path: str = "bot_database.db"):
        self.db_path = db_path
        self._connection: Optional[aiosqlite.Connection] = None
    
    async def connect(self) -> None:
        """Establish database connection and create tables."""
        self._connection = await aiosqlite.connect(self.db_path)
        self._connection.row_factory = aiosqlite.Row
        await self._create_tables()
        logger.info(f"Database connected: {self.db_path}")
    
    async def close(self) -> None:
        """Close database connection."""
        if self._connection:
            await self._connection.close()
            logger.info("Database connection closed")
    
    @property
    def connection(self) -> aiosqlite.Connection:
        """Get active database connection."""
        if not self._connection:
            raise RuntimeError("Database not connected. Call connect() first.")
        return self._connection
    
    async def _create_tables(self) -> None:
        """Create all required database tables."""
        await self.connection.executescript("""
            -- Users table
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                first_name TEXT,
                last_name TEXT,
                language_code TEXT DEFAULT 'en',
                preferred_model TEXT DEFAULT 'gpt-4o-mini',
                is_premium INTEGER DEFAULT 0,
                is_banned INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_active TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                message_count INTEGER DEFAULT 0,
                total_tokens_used INTEGER DEFAULT 0
            );
            
            -- Subscriptions table
            CREATE TABLE IF NOT EXISTS subscriptions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                subscription_type TEXT NOT NULL,
                stars_paid INTEGER NOT NULL,
                started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                expires_at TIMESTAMP NOT NULL,
                is_active INTEGER DEFAULT 1,
                telegram_payment_id TEXT,
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            );
            
            -- Conversations table (stores message history)
            CREATE TABLE IF NOT EXISTS conversations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                model_used TEXT,
                tokens_used INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            );
            
            -- Bot statistics table
            CREATE TABLE IF NOT EXISTS bot_stats (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                stat_date DATE UNIQUE DEFAULT (date('now')),
                total_messages INTEGER DEFAULT 0,
                total_users INTEGER DEFAULT 0,
                new_users INTEGER DEFAULT 0,
                openai_requests INTEGER DEFAULT 0,
                gemini_requests INTEGER DEFAULT 0,
                total_tokens INTEGER DEFAULT 0,
                total_revenue_stars INTEGER DEFAULT 0
            );
            
            -- Error logs table
            CREATE TABLE IF NOT EXISTS error_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                error_type TEXT NOT NULL,
                error_message TEXT NOT NULL,
                stack_trace TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            
            -- Payment history table
            CREATE TABLE IF NOT EXISTS payments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                amount_stars INTEGER NOT NULL,
                payment_type TEXT NOT NULL,
                telegram_payment_id TEXT,
                status TEXT DEFAULT 'pending',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            );
            
            -- Redeem codes table
            CREATE TABLE IF NOT EXISTS redeem_codes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                code TEXT UNIQUE NOT NULL,
                code_type TEXT NOT NULL,
                duration_days INTEGER DEFAULT 0,
                credits INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                expires_at TIMESTAMP,
                is_used INTEGER DEFAULT 0,
                used_by INTEGER,
                used_at TIMESTAMP,
                is_revoked INTEGER DEFAULT 0,
                created_by INTEGER,
                FOREIGN KEY (used_by) REFERENCES users(user_id),
                FOREIGN KEY (created_by) REFERENCES users(user_id)
            );

            -- Create indexes for better query performance
            CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);
            CREATE INDEX IF NOT EXISTS idx_conversations_user ON conversations(user_id);
            CREATE INDEX IF NOT EXISTS idx_subscriptions_user ON subscriptions(user_id);
            CREATE INDEX IF NOT EXISTS idx_subscriptions_active ON subscriptions(is_active);
            CREATE INDEX IF NOT EXISTS idx_stats_date ON bot_stats(stat_date);
            CREATE INDEX IF NOT EXISTS idx_redeem_codes_code ON redeem_codes(code);
            CREATE INDEX IF NOT EXISTS idx_redeem_codes_used ON redeem_codes(is_used);
        """)
        await self.connection.commit()
        logger.info("Database tables created/verified")
    
    async def execute(self, query: str, params: tuple = ()) -> aiosqlite.Cursor:
        """Execute a query and return cursor."""
        cursor = await self.connection.execute(query, params)
        await self.connection.commit()
        return cursor
    
    async def fetch_one(self, query: str, params: tuple = ()) -> Optional[aiosqlite.Row]:
        """Execute query and fetch one result."""
        cursor = await self.connection.execute(query, params)
        return await cursor.fetchone()
    
    async def fetch_all(self, query: str, params: tuple = ()) -> list:
        """Execute query and fetch all results."""
        cursor = await self.connection.execute(query, params)
        return await cursor.fetchall()

