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

urlpatterns = [
    path('movie/douban250/diff', movie_views.diff_douban_250),
    path('movie/local/collection/complete', movie_views.complete_local_movie_collection),
    path('tv/douban100/diff', tv_views.diff_douban_tv_show_100),
    path('tv/local/season/missing', tv_views.find_lost_local_season),
    path('tv/local/episode/missing', tv_views.find_lost_local_episode),
]
