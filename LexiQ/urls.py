"""
URL configuration for LexiQ project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.0/topics/http/urls/
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
from django.contrib import admin
from django.urls import path
from wordapp.views import upload_csv,index,upload_csv,display_words,start_game,delete_word_group,game,tts,play_audio


urlpatterns = [
    path("admin/", admin.site.urls),
    path('', index, name='index'),
    path('upload_csv/', upload_csv, name='upload_csv'),
    path('delete_word_group/', delete_word_group, name='delete_word_group'),

    path('display_words/', display_words, name='display_words'),
    path('start_game/', start_game, name='start_game'),
    path('game/<int:group_id>/', game, name='game'),
    path('tts/<str:word>/', tts, name='tts'),
    path('play-audio/<path:file_path>/', play_audio, name='play_audio'),
]
