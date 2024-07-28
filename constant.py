import os

user_agent = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36'

douban_cookie = os.environ.get('DOUBAN_COOKIE', '')
tmdb_api_key = os.environ.get('TMDB_API_KEY', '')
tmdb_image_path = 'https://image.tmdb.org/t/p/original'
tmdb_movie_path = 'https://www.themoviedb.org/movie'
tmdb_tv_path = 'https://www.themoviedb.org/tv'
bangumi_anime_path = 'https://bangumi.tv/subject'

movie_folder = '/Volumes/Movie/'
tv_folder = '/Volumes/TV/'
anime_folder = '/Volumes/Anime/'
music_folder = '/Volumes/Music/'
book_folder = '/Volumes/Book/'
