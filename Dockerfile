# Dockerfile
# Используем официальный Python-образ в качестве базового
FROM python:3.9-slim

# Устанавливаем рабочую директорию внутри контейнера
WORKDIR /app

# Копируем содержимое текущей директории в контейнер в /app
COPY . /app

# Устанавливаем необходимые пакеты из requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Открываем порт 5000 для доступа извне
EXPOSE 5000

# Запускаем main.py при старте контейнера
CMD ["python", "main.py"]
