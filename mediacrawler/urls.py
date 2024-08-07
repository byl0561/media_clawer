"""
URL configuration for mediacrawler project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.urls import path
import movie.views as movie_views
import tvshow.views as tv_views
import music.views as music_views
import book.views as book_views

urlpatterns = [
    path('movie/douban250/diff', movie_views.diff_douban_250),
    path('movie/local/collection/complete', movie_views.complete_local_movie_collection),
    path('movie/poster/<path:image_path>', movie_views.get_poster),
    path('tv/douban100/diff', tv_views.diff_douban_tv_show_100),
    path('tv/local/season/missing', tv_views.find_lost_tv_local_season),
    path('tv/local/episode/missing', tv_views.find_lost_tv_local_episode),
    path('tv/poster/<path:image_path>', tv_views.get_tv_poster),
    path('anime/bangumi/diff', tv_views.diff_bangumi_tv_anime_100),
    path('anime/local/season/missing', tv_views.find_lost_anime_local_season),
    path('anime/local/episode/missing', tv_views.find_lost_anime_local_episode),
    path('anime/poster/<path:image_path>', tv_views.get_anime_poster),
    path('album/douban250/diff', music_views.diff_douban_250),
    path('album/cover/<path:image_path>', music_views.get_cover),
    path('book/douban250/diff', book_views.diff_douban_250),
    path('book/cover/<path:image_path>', book_views.get_cover),
]
