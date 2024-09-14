FROM python:3.8-slim
LABEL authors="lava"

WORKDIR /app

RUN mkdir -p /Volumes/Movie /Volumes/TV /Volumes/Anime /Volumes/Music /Volumes/Book

RUN apt-get update && apt-get install -y cron
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt
COPY . /app

EXPOSE 8000
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]