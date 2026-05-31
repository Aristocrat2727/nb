FROM python:3.11-slim
WORKDIR /app
RUN pip install python-telegram-bot==20.7 requests==2.31.0
COPY bot.py .
CMD ["python", "bot.py"]
