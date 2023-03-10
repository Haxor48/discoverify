from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('home/', views.logged_in, name='logged-in'),
    path('findArtists/', views.find_artists, name='find-artists'),
    path('topArtists/', views.top_artists, name='top-artists'),
    path('topTracks/', views.top_tracks, name='top-tracks'),
    path('savedArtists/', views.saved_artists, name='saved-artists')
]
