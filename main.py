import logging
import asyncio
import os

from aiogram import Bot, Dispatcher
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from aiogram.filters import CommandStart
from aiogram import F
from dotenv import load_dotenv

from bot.handlers import router
from logging_config import setup_logging

# Load environment variables
load_dotenv("env.env")

# Initialize logging
setup_logging()
logger = logging.getLogger(__name__)

# bot = Bot(token=BOT_TOKEN)
botToken = os.getenv("BOT_TOKEN")
bot = Bot(token=botToken)
dp = Dispatcher()

from bot.models import user_models, MODELS

@dp.message(CommandStart())
async def start_cmd(message: Message):
    # Reset model choice on /start
    user_models.pop(message.from_user.id, None)
    
    # Create inline keyboard with model options
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=name, callback_data=model_id)]
        for model_id, name in MODELS.items() if "free" in name
    ])
    
    await message.reply(
        "Добро пожаловать! Выберите модель для генерации ответов:",
        reply_markup=keyboard
    )

@dp.callback_query(F.data.in_(MODELS.keys()))
async def model_selected(callback: CallbackQuery):
    user_id = callback.from_user.id
    model_id = callback.data
    user_models[user_id] = model_id
    logger.info(f"User {user_id} selected model {model_id}")
    await callback.message.edit_text(
        f"Выбрана модель: {MODELS[model_id]}\nТеперь можете задавать вопросы!"
    )
    await callback.answer()
    logger.debug(f"Model saved for user {user_id}: {user_models.get(user_id)}")

async def main():
    logger.info("Starting bot initialization...")
    
    dp.include_router(router)
    
    await bot.delete_webhook(drop_pending_updates=True)
    logger.info("Webhook deleted, starting polling...")
    
    await dp.start_polling(bot)
    logger.info("Bot stopped polling")

if __name__ == "__main__":
    asyncio.run(main())
