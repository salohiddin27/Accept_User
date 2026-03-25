import asyncio
import logging
import os
import re
from db import Database
from aiogram import Dispatcher, Bot
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import Message
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = os.getenv("ADMIN_ID")

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()
db = Database()


class Registration(StatesGroup):
    waiting_full_name = State()
    phone_number = State()


@dp.message(Command("start"))
async def start_handler(message: Message, state: FSMContext):
    if await db.check_user(message.from_user.id):
        await message.answer("Siz oldin ro'yxatdan o'tgansiz! ✅")
        return
    await message.answer("Welcome!\nCould you send me your Fullname?")
    await state.set_state((Registration.waiting_full_name))


@dp.message(Registration.waiting_full_name)
async def process_fullname(message: Message, state: FSMContext):
    full_name = message.text.strip()
    parts = full_name.split()
    if len(parts) < 2:
        await message.answer("Error! Please write your full name with a space (e.g., John Doe)")
        return
    first_name = parts[0].capitalize()
    last_name = " ".join(parts[1:]).title()
    await state.update_data(firstname=first_name, lastname=last_name, fullname=full_name)

    await state.set_state(Registration.phone_number)
    await message.answer(text="Please! Could you send men your phone number?")


@dp.message(Registration.phone_number)
async def process_phone_number(message: Message, state: FSMContext):
    number = message.text.strip()
    pattern = r"^\+998\d{9}$"
    if not re.match(pattern, number):
        await message.answer("Error! Please enter your number in +998XXXXXXXXX format.")
        return
    await state.update_data(number=number)

    user_data = await state.get_data()
    full_name = user_data.get('fullname')
    phone = user_data.get('number')
    try:
        await db.add_user(
            telegram_id=message.from_user.id,
            full_name=full_name,
            phone_number=phone
        )
        print(f"✅ User {full_name} bazaga saqlandi.")
    except Exception as e:
        logging.error(f"❌ Bazaga saqlashda xato: {e}")

    admin_text = (
        "🆕 Yangi foydalanuvchi ro'yxatdan o'tdi:\n\n"
        f"👤 Full_name: {full_name}\n"
        f"📞 Telefon: {phone}\n"
        f"🆔 User ID: {message.from_user.id}"
    )
    await bot.send_message(chat_id=int(ADMIN_ID), text=admin_text)
    await message.answer("✅ Thank you! Your information has been sent to the admin.")
    await state.clear()


async def main():
    logging.basicConfig(level=logging.INFO)
    await db.create_pool()  # Bazaga ulanish
    await db.create_table()  # Jadvalni tekshirish
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
