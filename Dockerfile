FROM python:3.9
LABEL authors="lava"

WORKDIR /app

RUN mkdir -p /Volumes/Movie /Volumes/TV /Volumes/Anime /Volumes/Music /Volumes/Book

COPY requirements.txt /app/
RUN pip install -r requirements.txt
COPY . /app

EXPOSE 8000
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]