<p>
<strong><h2>影视排行榜订阅比对器</h2></strong>
基于<strong>豆瓣</strong>、<strong>豆列</strong>、<strong>Bangumi</strong>等排行榜数据，比对NAS中存储的文件，给出维护建议。
</p>

### 电影

> 本地的电影需要使用 [tinyMediaManager](https://www.tinymediamanager.org/) 进行刮削，刮削器需要选择 [TMDB](https://www.themoviedb.org/)，刮削完成后需要整理文件

- 豆瓣电影TOP250：movie/douban250/diff

- 本地缺少的电影集：movie/local/collection/complete

### 电视剧

> 本地的电视剧需要使用 [tinyMediaManager](https://www.tinymediamanager.org/) 进行刮削，刮削器需要选择 [TMDB](https://www.themoviedb.org/)，刮削完成后需要整理文件。

- 豆列（电视剧TOP100 + 进10年点数据TOP100）：tv/douban100/diff

- 本地缺少的季：tv/local/season/missing

- 本地缺少的集：tv/local/episode/missing

### 动漫

> 本地的动漫需要使用 [tinyMediaManager](https://www.tinymediamanager.org/) 进行刮削，刮削器需要选择 [TMDB](https://www.themoviedb.org/)，刮削完成后需要整理文件。

- Bangumi TOP80 TV动漫：anime/bangumi/diff

- 本地缺少的季：anime/local/season/missing

- 本地缺少的集：anime/local/episode/missing

### 专辑

> 本地的专辑需要以 "{专辑名} - {音乐家} {年份}" 格式命名。例如：不能说的秘密 - 周杰伦 2007。

- 豆瓣专辑TOP250：album/douban250/diff

### 数据

> 本地的书籍需要使用 [calibre-web](https://github.com/janeczku/calibre-web) 进行管理。

- 豆瓣书籍TOP250：book/douban250/diff

### Docker部署

> 安装及配置 Docker 将不在此处说明，请自行解决

- 环境变量：
  - DEBUG：是否为debug模式 True/False
  - REDIS_HOST: Redis IP
  - REDIS_PORT: Redis 端口号，默认 6379
  - REDIS_PASS: Redis 密码，默认为空
  - DOUBAN_COOKIE：豆瓣 cookie，可解决某些 电影/电视剧 不可见的问题，非必需
  - TMDB_API_KEY：TMDB API 密钥，用于访问 TMDB 获取 电影/电视剧/动漫 元数据

- 文件夹：
  - 电影：/Volumes/Movie
  - 电视剧：/Volumes/TV
  - 动漫：/Volumes/Anime
  - 音乐专辑：/Volumes/Music
  - 图书：/Volumes/Book