from django.http import HttpResponse
from django.template import loader
from django.urls import resolve
from django.shortcuts import redirect
from . import api

def home(request):
    template = loader.get_template("index.html")
    return HttpResponse(template.render())

def logged_in(request):
    split = request.build_absolute_uri().split('home/')
    context = {
        'link': ''
    }
    if len(split) < 1 or split[1] == '':
        auth = api.authorize(split[0] + 'topArtists/')
        if len(auth) > 0:
            context['link'] = auth
            return redirect(auth)
    template = loader.get_template("loggedIn.html")
    return HttpResponse(template.render(context, request))

def find_artists(response):
    split = response.build_absolute_uri().split('findArtists/')
    context = {}
    if split[1] != '':
        if 'playlist' in split[1]:
            context['artists'] = api.create_recommended_playlist(response)
        else:
            context['artists'] =  api.recommend_artists(response)
            id = split[1].split('=')[1]
            api.like_artist(response, id, 'dislike' not in split[1])
    else:
        context['artists'] =  api.recommend_artists(response)
    template = loader.get_template("findArtists.html")
    return HttpResponse(template.render(context, response))

def top_artists(response):
    context = {
        'short_artists': api.get_top_artists(response, 'short'),
        'medium_artists': api.get_top_artists(response, 'medium'),
        'long_artists': api.get_top_artists(response, 'long')
    }
    template = loader.get_template("topArtists.html")
    return HttpResponse(template.render(context, response))

def top_tracks(response):
    context = {
        'short_songs': api.get_top_songs(response, 'short'),
        'medium_songs': api.get_top_songs(response, 'medium'),
        'long_songs': api.get_top_songs(response, 'long')
    }
    template = loader.get_template("topTracks.html")
    return HttpResponse(template.render(context, response))

def saved_artists(response):
    split = response.build_absolute_uri().split('findArtists/')
    if len(split) > 1 and split[1] != '':
        id = split[1].split('=')[1]
        if 'un' in id:
            api.unlike_artist(response, id, 'dislike' not in split[1])
        else:
            api.like_artist(response, id, 'dislike' not in split[1])
    context = {
        'liked_artists': api.get_liked_artists(response, True),
        'disliked_artists': api.get_liked_artists(response, False)
    }
    template = loader.get_template("savedArtists.html")
    return HttpResponse(template.render(context, response))