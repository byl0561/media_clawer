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
    apt-get install -y nginx ffmpeg && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*
COPY --from=frontend-build /app/dist /usr/share/nginx/html
COPY nginx/nginx.conf /etc/nginx/conf.d/default.conf
RUN touch /etc/nginx/auth.conf
RUN mkdir -p /Volumes/Movie /Volumes/TV /Volumes/Anime /Volumes/Music /Volumes/Book
WORKDIR /app
COPY backend/ .
RUN pip install --no-cache-dir -r requirements.txt
COPY docker-entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh
EXPOSE 8080
CMD ["/entrypoint.sh"]
