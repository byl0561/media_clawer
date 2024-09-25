FROM python:3.9-slim
LABEL authors="lava"

WORKDIR /app

RUN mkdir -p /Volumes/Movie /Volumes/TV /Volumes/Anime /Volumes/Music /Volumes/Book

RUN apt-get update && apt-get install -y cron
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt
COPY . /app

RUN python manage.py crontab add
RUN chmod +x start.sh
EXPOSE 8000
CMD ["/app/start.sh"]