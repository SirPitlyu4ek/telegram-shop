import asyncio
import os

from aiogram import Bot, Dispatcher
from aiogram.filters import CommandStart
from aiogram.types import (
    Message,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    WebAppInfo,
)
from dotenv import load_dotenv


load_dotenv()

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
WEB_APP_URL = os.getenv("WEB_APP_URL")

if not BOT_TOKEN:
    raise RuntimeError("TELEGRAM_BOT_TOKEN не заданий у .env")

if not WEB_APP_URL:
    raise RuntimeError("WEB_APP_URL не заданий у .env")


bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()


@dp.message(CommandStart())
async def start_command(message: Message):
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🛒 Відкрити магазин",
                    web_app=WebAppInfo(url=WEB_APP_URL),
                )
            ]
        ]
    )

    await message.answer(
        "Вітаю! Натисніть кнопку нижче, щоб відкрити магазин.",
        reply_markup=keyboard,
    )


async def main():
    print("Telegram bot started")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())