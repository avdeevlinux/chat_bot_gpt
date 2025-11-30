# Берем легкую версию Python
FROM python:3.12-slim

# Устанавливаем рабочую папку внутри контейнера
WORKDIR /app/

RUN python -m pip install --upgrade pip

# Установка системных зависимостей для компиляции пакетов и Playwright
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libxml2-dev \
    libxslt1-dev \
    libxml2 \
    libxslt1.1 \
    ca-certificates \
    fonts-liberation \
    libasound2 \
    libatk-bridge2.0-0 \
    libatk1.0-0 \
    libatspi2.0-0 \
    libcairo-gobject2 \
    libcairo2 \
    libcups2 \
    libdbus-1-3 \
    libdrm2 \
    libexpat1 \
    libgbm1 \
    libgcc1 \
    libglib2.0-0 \
    libgtk-3-0 \
    libnspr4 \
    libnss3 \
    libpango-1.0-0 \
    libpangocairo-1.0-0 \
    libstdc++6 \
    libx11-6 \
    libx11-xcb1 \
    libxcb1 \
    libxcomposite1 \
    libxcursor1 \
    libxdamage1 \
    libxext6 \
    libxfixes3 \
    libxi6 \
    libxrandr2 \
    libxrender1 \
    libxss1 \
    libxtst6 \
    lsb-release \
    wget \
    xdg-utils \
    && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Копируем список зависимостей и ставим их
COPY requirements.txt .
RUN python -m pip install -r requirements.txt
RUN playwright install chromium

# Копируем наши файлы в контейнер
COPY ./ .

# Запускаем основной файл
CMD ["python", "main.py"]
