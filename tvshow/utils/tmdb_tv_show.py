import requests
from datetime import datetime
from constant import *
from tvshow.models.tvshow import TmdbTvShow, TmdbSeason, Rate, TmdbEpisode


def get_tmdb_tv_show(tv_show_id: int) -> TmdbTvShow:
    url = f'https://api.themoviedb.org/3/tv/{tv_show_id}?api_key={tmdb_api_key}&language=zh-CN'
    response = requests.get(url)

    if response.status_code == 200:
        data = response.json()
        season_datas = data['seasons']
        seasons = []
        for season_data in season_datas:
            season = TmdbSeason(season_data['season_number'],
                                season_data['name'],
                                season_data['air_date'],
                                [])
            seasons.append(season)

        seasons = sorted(seasons, key=lambda x: x.num)
        return TmdbTvShow(data['name'],
                          data['original_name'],
                          [int(datetime.strptime(data['first_air_date'], "%Y-%m-%d").year if len(data['first_air_date']) > 0 else 0),
                           int(datetime.strptime(data['last_air_date'], "%Y-%m-%d").year if len(data['last_air_date']) > 0 else 0)],
                          data['original_language'],
                          data['poster_path'],
                          Rate(data['vote_average'], data['vote_count'], 'TMDB'),
                          data['id'],
                          seasons)
    else:
        print('Failed to fetch data')
        return None


def get_tmdb_tv_show_season(tv_show_id: int, season_num: int) -> TmdbSeason:
    url = f'https://api.themoviedb.org/3/tv/{tv_show_id}/season/{season_num}?api_key={tmdb_api_key}&language=zh-CN'
    response = requests.get(url)

    if response.status_code == 200:
        data = response.json()
        episode_datas = data['episodes']
        episodes = []

        for episode_data in episode_datas:
            episode = TmdbEpisode(episode_data['episode_number'],
                                  episode_data['name'],
                                  episode_data['air_date'],
                                  episode_data['runtime'])
            episodes.append(episode)

        episodes = sorted(episodes, key=lambda x: x.num)
        return TmdbSeason(season_num,
                          data['name'],
                          data['air_date'],
                          episodes)

    else:
        print('Failed to fetch data')
        return None