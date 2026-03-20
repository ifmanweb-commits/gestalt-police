FROM python:3.14-slim

# Установка build-essential для компиляции C-расширений
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Настройка зеркал PyPI для стабильной загрузки
RUN pip config set global.index-url https://mirrors.cloud.tencent.com/pypi/simple/ && \
    pip config set global.trusted-host mirrors.cloud.tencent.com && \
    pip config set global.timeout 120

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["python", "vk_bot.py"]