# 构建前端应用
FROM node:18 AS frontend-build
WORKDIR /app
COPY frontend/ .
RUN npm install
RUN npm run build

# 后端镜像
FROM python:3.9-slim
LABEL authors="lava"
RUN apt-get update && \
    apt-get install -y cron nginx && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*
COPY --from=frontend-build /app/dist /usr/share/nginx/html
COPY nginx/nginx.conf /etc/nginx/conf.d/default.conf
# Safe default so nginx starts even if the entrypoint is bypassed (e.g. an
# overridden container command): empty == auth disabled. The entrypoint
# overwrites this from APP_USERNAME / APP_PASSWORD at start.
RUN touch /etc/nginx/auth.conf
RUN mkdir -p /Volumes/Movie /Volumes/TV /Volumes/Anime /Volumes/Music /Volumes/Book
WORKDIR /app
COPY backend/ .
RUN pip install --no-cache-dir -r requirements.txt
RUN python manage.py crontab add
COPY docker-entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh
EXPOSE 8080
# gunicorn (sync workers) instead of `runserver`: production-grade, and each
# worker is a single-threaded process so the per-request NAS-scan
# multiprocessing.Pool no longer forks from a multithreaded server. The
# entrypoint also generates the site-wide Basic Auth files from env.
CMD ["/entrypoint.sh"]