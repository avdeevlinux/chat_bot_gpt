import logging
from pathlib import Path

def setup_logging():
    # Создаем директорию для логов, если её нет
    logs_dir = Path("logs")
    logs_dir.mkdir(exist_ok=True)
    
    # Настройка основного логгера
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.FileHandler("logs/bot.log", encoding="utf-8"),
            logging.StreamHandler()
        ]
    )

    # Настройка логгера для запросов к GPT
    gpt_logger = logging.getLogger("gpt")
    gpt_logger.setLevel(logging.DEBUG)
    gpt_handler = logging.FileHandler("logs/gpt_requests.log", encoding="utf-8")
    gpt_handler.setFormatter(logging.Formatter("%(asctime)s - %(message)s"))
    gpt_logger.addHandler(gpt_handler)
