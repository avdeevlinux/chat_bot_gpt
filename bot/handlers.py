import re
import logging

from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import CommandStart
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext

from bot.gpt import gpt_request, split_text
from bot.models import user_models, MODELS

router = Router()
logger = logging.getLogger(__name__)

# Debug: Check if user_models is the same object across imports
import bot.models
logger.debug(f"Handlers user_models id: {id(user_models)}, module user_models id: {id(bot.models.user_models)}")

router = Router()
logger = logging.getLogger(__name__)

class StateGpt(StatesGroup):
  text = State()

@router.message(StateGpt.text)
async def state_answer(message: Message):
    await message.reply("Пожалуйста, дождитесь ответа!")

@router.message(F.text)
async def gpt_work(message: Message, state: FSMContext):
    await state.set_state(StateGpt.text)
    
    user_id = message.from_user.id
    model_id = user_models.get(user_id)
    
    logger.info(f"New message from user {user_id}: {message.text[:50]}...")
    logger.debug(f"Current models state: {user_models}")
    
    if not model_id:
        logger.warning(f"User {user_id} tried to send message without selecting model")
        logger.debug(f"Available models: {MODELS}")
        await message.reply("Пожалуйста, сначала выберите модель с помощью команды /start")
        await state.clear()
        return
    
    logger.debug(f"User {user_id} using model {model_id}")
    answer = await message.reply("Ответ генерируется...")
    
    try:
        logger.info(f"Processing GPT request for user {user_id}")
        response = await gpt_request(message.text, model=model_id)
        logger.debug(f"GPT response received for user {user_id}")
        
        response_text = remove_markdown(response.choices[0].message.content)
        # Calculate prefix length for part indicator "(X/Y) "
        max_parts = len(str((len(response_text) // 4000) + 1))
        prefix_len = len(f"(1/{max_parts}) ")
        chunks = split_text(response_text, max_length=4000, prefix_length=prefix_len)
        
        if len(chunks) == 0:
            await answer.edit_text("Пустой ответ от GPT")
            return
        
        # Edit initial message with first chunk
        try:
            await answer.edit_text(f"(1/{len(chunks)}) {chunks[0]}")
        except Exception as e:
            logger.error(f"Error sending first chunk to user {user_id}: {str(e)}", exc_info=True)
            await answer.edit_text(f"Произошла ошибка при отправке ответа: {str(e)}")
            return
        
        # Send remaining chunks as new messages
        for i, chunk in enumerate(chunks[1:], 2):
            try:
                await message.reply(f"({i}/{len(chunks)}) {chunk}")
            except Exception as e:
                logger.error(f"Error sending chunk {i} to user {user_id}: {str(e)}", exc_info=True)
                await message.reply(f"Произошла ошибка при отправке части ответа: {str(e)}")

    except Exception as e:
        logger.error(f"Error processing request for user {user_id}: {str(e)}", exc_info=True)
        if "RateLimitError" in str(e):
            await answer.edit_text(f"Произошла ошибка: Слишком много запросов. Пожалуйста, попробуйте позже или добавьте свой собственный ключ API: https://openrouter.ai/settings/integrations")
        else:
            await answer.edit_text(f"Произошла ошибка: {str(e)}")
    finally:
        await state.clear()
        logger.debug(f"Request processing completed for user {user_id}")


def remove_markdown(text):
    # Удаление заголовков (###, ##, #)
    text = re.sub(r'#+\s*', '', text)
    
    # Удаление жирного и курсивного текста (**...**, *...*, __...__, _..._)
    text = re.sub(r'(\*\*|__)(.*?)\1', r'\2', text)
    text = re.sub(r'(\*|_)(.*?)\1', r'\2', text)
    
    # Удаление зачеркнутого текста (~~...~~)
    text = re.sub(r'~~(.*?)~~', r'\1', text)
    
    # Удаление ссылок ([текст](URL)) и изображений (![alt](URL))
    # text = re.sub(r'!?\[(.*?)\]\(.*?\)', r'\1', text)
    
    # Удаление инлайн-кода (`...`)
    # text = re.sub(r'`(.*?)`', r'\1', text)
    
    # Удаление блоков кода (```...```, ~~~...~~~)
    # text = re.sub(r'```.*?\n(.*?)```', r'\1', text, flags=re.DOTALL)
    # text = re.sub(r'~~~.*?\n(.*?)~~~', r'\1', text, flags=re.DOTALL)
    
    # Удаление HTML-тегов (если есть)
    text = re.sub(r'<[^>]+>', '', text)
    
    # Удаление горизонтальных линий (---, ***, ___)
    text = re.sub(r'^[-*_]{3,}$', '', text, flags=re.MULTILINE)
    
    # Удаление маркированных списков (+, -, *)
    # text = re.sub(r'^[\s]*[-*+]\s+', '', text, flags=re.MULTILINE)
    
    # Удаление нумерованных списков (1., 2., ...)
    # text = re.sub(r'^[\s]*\d+\.\s+', '', text, flags=re.MULTILINE)
    
    # Удаление лишних пробелов и переносов строк
    text = re.sub(r'\n\s*\n', '\n\n', text).strip()
    
    return text
