<h2 align="center">影视排行榜订阅比对器</h2>

<p align="center">
基于 <strong>豆瓣</strong>、<strong>豆列</strong>、<strong>Bangumi</strong> 等排行榜数据，比对 NAS 中已存储的媒体文件，给出收藏维护建议。
</p>

---

## 这是什么

一个自部署的小工具。它抓取主流榜单（豆瓣电影 TOP250、豆列电视剧、Bangumi 动画、豆瓣专辑/书籍 TOP250），与本地 NAS 上的影视/音乐/图书做模糊比对，在网页上给出维护建议：

- **缺少（最新）**：榜单上有、本地没有的，建议补全
- **过时**：本地有、已跌出榜单且评分不再突出的，建议清理
- **续集/缺集**：本地已有的系列/剧集，TMDB 上存在尚未收录的续作、季或集

网页提供「库维护概览」首页，点击某类媒体进入海报网格查看明细；卡片可跳转豆瓣 / TMDB / Bangumi 详情页。

## 整体架构

```
                         ┌─────────────────────────────────────────────┐
                         │              Docker 容器 (:8080)             │
   浏览器                 │                                              │
   ──────►  Nginx :8080 ──┼─►  /            静态资源 (Vue 构建产物)        │
            (剥离 /api/)   │   /api/v1/  ──► gunicorn → Django :8000      │
                         │                    │                         │
                         │                    ├─► 豆瓣 / Bangumi 抓取     │
                         │                    ├─► TMDB API（带限速重试）   │
                         │                    ├─► 扫描 /Volumes/* 本地库   │
                         │                    └─► Redis（上游响应缓存）     │
                         │                django-crontab 每周预热上游缓存   │
                         └─────────────────────────────────────────────┘
```

整个应用打包为**单个 Docker 镜像**。Nginx 托管前端静态资源，并把 `/api/` 反向代理到 gunicorn 上的 Django（代理时剥离 `/api/` 前缀，故 Django 实际匹配 `v1/...`）。Nginx 启用 SPA history 回退（`try_files … /index.html`），并把 `/api/` 反代超时对齐到 300s（与 gunicorn `--timeout`、前端 axios 一致）。

### 后端（`backend/`，Django 4.2 + DRF / Python 3.9）

- **`core/` 共享包**：`conf`（配置单一来源）、`http`（带 Redis 缓存的 GET；TMDB 专用有界重试，识别 429/瞬时错误，遵循 `Retry-After`，指数退避）、`scanning`（多进程扫库，卷缺失即返回空而非崩溃）、`images`（路径穿越安全的图片流式响应）、`matching`（通用模糊比对内核）、`exceptions`、`serializers`、`cron`。
- **4 个轻应用** `movie / tvshow / music / book`，结构统一：`models.py`（纯数据类）、`crawlers/`（douban/tmdb/bangumi/local）、`matching.py`、`services.py`（业务编排）、`serializers.py`（DRF）、`views.py`（DRF `APIView`）、`cron.py`。动漫由 `tvshow` 应用对 anime 库提供。
- **无数据库**：不使用 ORM、无 migrations，数据全部实时抓取。
- **OpenAPI**：drf-spectacular 自动生成 schema 与 Swagger UI。

### 缓存与时效（重要）

- **diff 结果不缓存**，每次请求实时重算（重新扫 NAS + 重新比对）。
- **上游响应缓存**：豆瓣 HTML / Bangumi / TMDB JSON 缓存于 Redis，默认 **8 天**（`SOURCE_CACHE_TTL_MINUTES`，大于每周 cron 间隔，保证两次预热之间不过期）。
- **cron 每周预热**上游缓存，使正常请求始终命中缓存、不实时抓站。
- 上游抓取整体失败（列表为空）时返回 **HTTP 503**，而非把整库误判为「过时」。
- 因此榜单数据最长约有一周滞后——这是「请求不阻塞」的取舍。

### 前端（`frontend/`，Vue 3 + TypeScript + Vite + Tailwind）

- **路由**（vue-router，history 模式）：`/` 为库维护概览（各媒体类型汇总卡，显示缺口计数）；`/library/:type` 为该类型的分段标签（最新 / 续集 / 过时，带计数）+ 响应式海报网格。桌面与移动端自适应。
- **状态**：`stores/mediaCatalog` 单例复用各媒体 hook 的记忆化加载，概览页与详情页共享同一请求；点「刷新」统一失效重拉。
- 暗色靛紫设计令牌（Tailwind），骨架 / 空 / 错误态；每个 diff 每次加载只请求一次，由相关标签页复用同一响应。

## API 接口

RESTful、带版本前缀。下表为浏览器侧路径（经 Nginx）：

| 方法 | 路径 | 响应 |
| ---- | ---- | ---- |
| GET | `/api/v1/movies/diff` | `{ missing: [], extra: [] }` |
| GET | `/api/v1/movies/collection-gaps` | `[{ collection, missing: [] }]` |
| GET | `/api/v1/tv-shows/diff` | `{ missing, extra }` |
| GET | `/api/v1/tv-shows/local-gaps` | `[{ show, missing_seasons, incomplete_seasons }]` |
| GET | `/api/v1/anime/diff` | `{ missing, extra }` |
| GET | `/api/v1/anime/local-gaps` | `[{ show, missing_seasons, incomplete_seasons }]` |
| GET | `/api/v1/albums/diff` | `{ missing, extra }` |
| GET | `/api/v1/books/diff` | `{ missing, extra }` |
| GET | `/api/v1/{movies,tv-shows,anime}/poster/<path>`、`/api/v1/{albums,books}/cover/<path>` | 本地海报/封面图片流 |
| GET | `/api/v1/schema/` | OpenAPI schema |
| GET | `/api/v1/docs/` | Swagger UI |

> `local-gaps` 合并了原「缺少的季」与「缺少的集」：`missing_seasons` 为整季缺失，`incomplete_seasons` 为已有但集数落后。

## 本地媒体规范

- **电影 / 电视剧 / 动漫**：用 [tinyMediaManager](https://www.tinymediamanager.org/) 或 [MoviePilot](https://github.com/jxxghp/MoviePilot) 刮削，刮削源选 [TMDB](https://www.themoviedb.org/)，刮削后整理文件（生成 `.nfo`、`poster.*`）。
  - 电影 NFO 文件名兼容两种约定：tmm 的 `movie.nfo` 与 MoviePilot 的 `{title} ({year}).nfo`；同目录两者并存时以 MoviePilot 的为准。
  - 电视剧/动漫沿用 Kodi 标准：`tvshow.nfo` + `Season N/` + 集 NFO（任意名，需含 `<season>` / `<episode>` / `<title>` / `<aired>` 或 `<premiered>` / `<runtime>` 字段）。第 0 季文件夹兼容 `Specials/`（tmm 默认）与 `Season 0/`（MoviePilot 默认）。
  - **中文别名补充**：TMDB 未收录中文翻译的片（典型如日剧/韩剧/小众片）`<title>` 会是原始语言，与榜单中文标题文本匹配失败。在该片所在目录放一个 `alias.txt`，每行写一个中文别名，扫库时会作为额外标题加入匹配，电影/电视剧/动漫均支持。例：`/media/tv/30歳まで.../alias.txt` 写 `30岁的童贞魔法师`。
    - Bangumi 动画榜单里被截断的标题（如 `物语`、`86`）会导致你已拥有的番被误报为缺失——把截断标题作为别名绑到对应番剧目录即可命中，无需改代码。
- **音乐专辑**：目录命名 `{专辑名} - {音乐家} {年份}`，如 `不能说的秘密 - 周杰伦 2007`。
- **图书**：用 [calibre-web](https://github.com/janeczku/calibre-web) 管理。
- **库级忽略榜单条目**：在任一媒体库**根目录**放一个 `.mediaclawer.json`，写 `exclude_titles`，命中的榜单条目不再出现在该库的「缺失」列表。标题按双向子串匹配（写短主标题 `银魂` 即可命中 `银魂：完结篇`）。电影/电视剧/动漫/专辑/图书均支持，改完即时生效、无需重新部署。内置默认仍排除长篇动画（`死神/银魂/航海王/瑞克和莫蒂`）与工具书（`中国少年儿童百科全书/十万个为什么`），此文件中的条目在默认之上追加。例：

  ```json
  // /Volumes/Anime/.mediaclawer.json
  { "exclude_titles": ["名侦探柯南", "蜡笔小新"] }
  ```

## Docker 部署

> Docker 安装与配置请自行解决。

```bash
docker build -t media-crawler .
docker run -d -p 8080:8080 \
  -e REDIS_HOST=<redis-ip> \
  -e TMDB_API_KEY=<your-tmdb-key> \
  -v /path/to/Movie:/Volumes/Movie \
  -v /path/to/TV:/Volumes/TV \
  -v /path/to/Anime:/Volumes/Anime \
  -v /path/to/Music:/Volumes/Music \
  -v /path/to/Book:/Volumes/Book \
  media-crawler
```

访问 `http://<host>:8080`，接口文档 `http://<host>:8080/api/v1/docs/`。

### 环境变量

| 变量 | 说明 | 默认值 |
| ---- | ---- | ---- |
| `DEBUG` | 是否 debug 模式（值为 `true` 时开启，大小写不敏感） | `false` |
| `DJANGO_SECRET_KEY` | Django 密钥，生产环境务必覆盖 | 内置不安全默认值 |
| `ALLOWED_HOSTS` | 允许的 Host，逗号分隔 | `*` |
| `REDIS_HOST` | Redis IP | （必填，用于缓存） |
| `REDIS_PORT` | Redis 端口 | `6379` |
| `REDIS_PASS` | Redis 密码 | 空 |
| `DOUBAN_COOKIE` | 豆瓣 cookie，可解决部分条目不可见问题 | 非必需 |
| `TMDB_API_KEY` | TMDB API 密钥 | 非必需但强烈建议 |
| `CRAWLER_USER_AGENT` | 抓取使用的 UA | 内置 Chrome UA |
| `MOVIE_FOLDER` / `TV_FOLDER` / `ANIME_FOLDER` / `MUSIC_FOLDER` / `BOOK_FOLDER` | 各媒体库路径 | `/Volumes/Movie/` 等 |
| `HTTP_READ_TIMEOUT` | 出站请求读超时（秒，连接超时固定 5s） | `30` |
| `SCAN_WORKERS` | 扫库进程数 | `min(8, CPU)` |
| `TMDB_MAX_RETRIES` | TMDB 限速/瞬时错误额外重试次数 | `3` |
| `SOURCE_CACHE_TTL_MINUTES` | 上游响应缓存时长（分钟） | `11520`（8 天） |
| `GUNICORN_WORKERS` | gunicorn worker 数 | `3` |
| `GUNICORN_TIMEOUT` | gunicorn 请求超时（秒） | `300` |

### 挂载目录

| 容器内路径 | 用途 |
| ---- | ---- |
| `/Volumes/Movie` | 电影 |
| `/Volumes/TV` | 电视剧 |
| `/Volumes/Anime` | 动漫 |
| `/Volumes/Music` | 音乐专辑 |
| `/Volumes/Book` | 图书 |

### 定时刷新

容器内 cron 每周凌晨 4:30 预热各类上游缓存：图书（周一）、电影（周二）、音乐（周三）、电视剧/动漫（周四），配置见 `settings.py` 的 `CRONJOBS`。

## 本地开发

后端：

```bash
cd backend
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
# 需可访问 Redis
gunicorn mediacrawler.wsgi:application --bind 0.0.0.0:8000   # 或 python manage.py runserver
```

前端：

```bash
cd frontend
npm install
npm run dev       # 开发服务器
npm run build     # 生产构建（含 type-check），产物在 dist/
```

## 技术栈

- **后端**：Django 4.2、Django REST Framework、drf-spectacular、Python 3.9、requests、BeautifulSoup4 / lxml、django-redis、django-crontab、gunicorn
- **前端**：Vue 3、TypeScript、Vite、vue-router、Tailwind CSS、axios
- **部署**：多阶段 Docker（Node 18 构建前端 + python:3.9-slim 运行）、Nginx、gunicorn、Redis

## License

见 [LICENSE](LICENSE)。
