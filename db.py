import asyncpg
import os
from dotenv import load_dotenv

load_dotenv()

class Database:
    def __init__(self):
        self.pool = None

    async def create_pool(self):
        """Bazaga ulanish hovuzini (pool) yaratish"""
        self.pool = await asyncpg.create_pool(
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASS"),
            database=os.getenv("DB_NAME"),
            host=os.getenv("DB_HOST"),
            port=os.getenv("DB_PORT")
        )

    async def create_table(self):
        """Jadval yaratish (agar yo'q bo'lsa)"""
        async with self.pool.acquire() as connection:
            await connection.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    telegram_id BIGINT PRIMARY KEY,
                    full_name VARCHAR(255),
                    phone_number VARCHAR(20),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)

    async def check_user(self, telegram_id):
        """Foydalanuvchini tekshirish"""
        async with self.pool.acquire() as connection:
            user = await connection.fetchrow(
                "SELECT * FROM users WHERE telegram_id = $1", telegram_id
            )
            return user is not None

    async def add_user(self, telegram_id, full_name, phone_number):
        """Yangi foydalanuvchi qo'shish"""
        async with self.pool.acquire() as connection:
            await connection.execute(
                "INSERT INTO users (telegram_id, full_name, phone_number) VALUES ($1, $2, $3)",
                telegram_id, full_name, phone_number
            )