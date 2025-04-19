FROM python:3.11-slim

# Устанавливаем рабочую директорию в контейнере
WORKDIR /app

# Устанавливаем переменные окружения
# PYTHONDONTWRITEBYTECODE: Предотвращает запись .pyc файлов
# PYTHONUNBUFFERED: Выводит логи без буферизации для наблюдения в реальном времени
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Устанавливаем зависимости
# Сначала копируем только файл с зависимостями для использования кэша Docker
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копируем проектные файлы
COPY . .

# Создаем пользователя без root-доступа для повышения безопасности
RUN adduser --disabled-password --gecos "" appuser && \
    chown -R appuser:appuser /app
USER appuser

# Открываем порт для доступа к приложению
EXPOSE 8000

# Запускаем команду по умолчанию
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"] 