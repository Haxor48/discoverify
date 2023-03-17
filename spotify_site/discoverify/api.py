import spotipy
from spotipy.oauth2 import SpotifyOAuth
from pathlib import Path
import os
from collections import namedtuple
import sqlite3

Artist = namedtuple('Artist', ['name', 'image_url'])
RecommendArtist = namedtuple('RecommendArtist', ['name', 'image_url', 'id'])
ArtistCalc = namedtuple('ArtistCalc', ['id', 'score'])
Song = namedtuple('Song', ['name', 'artist', 'image_url'])

SPOTIPY_CLIENT_ID = 'e2727b5e29274e5fb905ccdead5e823a'
SPOTIPY_CLIENT_SECRET = '213c52c5d65f4fe181682134dce496e1'
SPOTIPY_REDIRECT_URI = 'http://18.119.126.8:8000/topArtists/'

scope = 'playlist-read-private playlist-modify-private user-top-read'

def authorize(url: str) -> str:
    reader = Path('./discoverify/data/credentials.txt').open('r')
    read = reader.read().split('\n')
    reader.close()
    os.environ['SPOTIPY_CLIENT_ID'] = read[0]
    os.environ['SPOTIPY_CLIENT_SECRET'] = read[1]
    os.environ['SPOTIPY_REDIRECT_URI'] = url
    oauth = SpotifyOAuth(client_id = SPOTIPY_CLIENT_ID, client_secret = SPOTIPY_CLIENT_SECRET, redirect_uri = SPOTIPY_REDIRECT_URI, scope=scope, cache_path=".cache-")
    token = oauth.get_cached_token()
    if not token:
        auth_url = oauth.get_authorize_url()
        return auth_url
    return ''

def get_top_artists(request, time: str) -> list[Artist]:
    base = request.build_absolute_uri().split('topArtists')[0]
    token = '{}topArtists/?{}'.format(base, request.GET.urlencode())
    reader = Path('./discoverify/data/credentials.txt').open('r')
    read = reader.read().split('\n')
    reader.close()
    oauth = SpotifyOAuth(client_id = read[0], client_secret = read[1], redirect_uri = base + 'topArtists/', scope=scope, cache_path=".cache-")
    code = oauth.parse_response_code(token)
    token_info = oauth.get_access_token(code)
    output = []
    if token_info:
        sp = spotipy.Spotify(auth = token_info['access_token'])
        top_artists = sp.current_user_top_artists(limit=20, time_range=f'{time}_term')['items']
        for artist in top_artists:
            output.append(Artist(artist['name'], artist['images'][0]['url']))
    return output

def get_top_songs(request, time: str) -> list[Song]:
    base = request.build_absolute_uri().split('topArtists')[0]
    token = '{}topArtists/?{}'.format(base, request.GET.urlencode())
    reader = Path('./discoverify/data/credentials.txt').open('r')
    read = reader.read().split('\n')
    reader.close()
    oauth = SpotifyOAuth(client_id = read[0], client_secret = read[1], redirect_uri = base + 'topArtists/', scope=scope, cache_path=".cache-")
    code = oauth.parse_response_code(token)
    token_info = oauth.get_access_token(code)
    output = []
    if token_info:
        sp = spotipy.Spotify(auth = token_info['access_token'])
        songs = sp.current_user_top_tracks(limit = 20, time_range=f'{time}_term')['items']
        for song in songs:
            artists = ''
            for artist in song['artists']:
                artists += artist['name'] + ', '
            artists = artists[:-2]
            output.append(Song(song['name'], artists, song['album']['images'][0]['url']))
    return output

def _add_artist(artists, artist):
    if len(artists) == 0 or artist.score < artists[-1].score:
        artists.append(artist)
        return
    if artist.score > artists[0].score:
        artists.insert(0, artist)
        return
    for i in range(len(artists)-1, 1, -1):
        if artist.score < artists[i-1].score:
            artists.insert(i, artist)
            return
    '''if len(artists) == 0:
        artists.append(artist)
        return
    left = 0
    right = len(artists)-1
    if artist.score < artists[right].score:
        artists.append(artist)
        return
    if artist.score > artists[left].score:
        artists.insert(0, artist)
        return
    while left < right:
        middle = (left + right) // 2
        if artist.score < artists[middle].score:
            left = middle
        else:
            if artists[middle-1].score > artist.score:
                artists.insert(middle, artist)
                return
            else:
                right = middle'''

def _get_top_in_dict(sp, recommended_artists) -> list[RecommendArtist]:
    output = []
    top_artists = []
    for key in recommended_artists.keys():
        if len(top_artists) < 20:
            _add_artist(top_artists, ArtistCalc(key, recommended_artists[key]))
        elif recommended_artists[key] > top_artists[-1].score:
            top_artists.pop()
            _add_artist(top_artists, ArtistCalc(key, recommended_artists[key]))
    for artist in top_artists:
        info = sp.artist(artist.id)
        output.append(RecommendArtist(info['name'], info['images'][0]['url'], artist.id))
    return output
        

def recommend_artists(request) -> list[RecommendArtist]:
    base = request.build_absolute_uri().split('topArtists')[0]
    token = '{}topArtists/?{}'.format(base, request.GET.urlencode())
    reader = Path('./discoverify/data/credentials.txt').open('r')
    read = reader.read().split('\n')
    reader.close()
    oauth = SpotifyOAuth(client_id = read[0], client_secret = read[1], redirect_uri = base + 'topArtists/', scope=scope, cache_path=".cache-")
    code = oauth.parse_response_code(token)
    token_info = oauth.get_access_token(code)
    output = []
    if token_info:
        sp = spotipy.Spotify(auth = token_info['access_token'])
        short_artists = sp.current_user_top_artists(limit=20, time_range='short_term')['items']
        med_artists = sp.current_user_top_artists(limit=20, time_range='medium_term')['items']
        long_artists = sp.current_user_top_artists(limit=20, time_range='long_term')['items']
        user = sp.current_user()
        no_recommend = set()
        for artist in short_artists:
            if artist['id'] not in no_recommend:
                no_recommend.add(artist['id'])
        for artist in med_artists:
            if artist['id'] not in no_recommend:
                no_recommend.add(artist['id'])
        for artist in long_artists:
            if artist['id'] not in no_recommend:
                no_recommend.add(artist['id'])
        liked_artists = []
        connection = sqlite3.connect('./discoverify/user_info.db')
        cursor = connection.execute('''
                                SELECT *
                                FROM user_info
                                WHERE user_id = ?;''', (user['id'],))
        info = cursor.fetchone()
        cursor.close()
        if info is not None:
            if len(info[1]) > 0:
                liked_artists = info[1].split(',')
                for artist in liked_artists:
                    if artist not in no_recommend:
                        no_recommend.add(artist)
            if len(info[2]) > 0:
                disliked_artists = info[2].split(',')
                for artist in disliked_artists:
                    if artist not in no_recommend:
                        no_recommend.add(artist)
        recommend_artists = {}
        used_artists = set()
        for i in range(len(short_artists)):
            if short_artists[i]['id'] not in used_artists:
                used_artists.add(short_artists[i]['id'])
                similar_artists = sp.artist_related_artists(short_artists[i]['id'])['artists']
                if len(similar_artists) > 10:
                    similar_artists = similar_artists[:10]
                for j in range(len(similar_artists)):
                    if similar_artists[j]['id'] not in no_recommend:
                        if similar_artists[j]['id'] not in recommend_artists:
                            recommend_artists[similar_artists[j]['id']] = (20-j) * (20-i)
                        else:
                            recommend_artists[similar_artists[j]['id']] += (20-i) * (20-j)
            if med_artists[i]['id'] not in used_artists:
                used_artists.add(med_artists[i]['id'])
                similar_artists = sp.artist_related_artists(med_artists[i]['id'])['artists']
                if len(similar_artists) > 10:
                    similar_artists = similar_artists[:10]
                for j in range(len(similar_artists)):
                    if similar_artists[j]['id'] not in no_recommend:
                        if similar_artists[j]['id'] not in recommend_artists:
                            recommend_artists[similar_artists[j]['id']] = (20-j) * (20-i)
                        else:
                            recommend_artists[similar_artists[j]['id']] += (20-i) * (20-j)
            if long_artists[i]['id'] not in used_artists:
                used_artists.add(long_artists[i]['id'])
                similar_artists = sp.artist_related_artists(long_artists[i]['id'])['artists']
                if len(similar_artists) > 10:
                    similar_artists = similar_artists[:10]
                for j in range(len(similar_artists)):
                    if similar_artists[j]['id'] not in no_recommend:
                        if similar_artists[j]['id'] not in recommend_artists:
                            recommend_artists[similar_artists[j]['id']] = (20-j) * (20-i)
                        else:
                            recommend_artists[similar_artists[j]['id']] += (20-i) * (20-j)
        for i in range(len(liked_artists)):
            if liked_artists[i] not in used_artists:
                used_artists.add(liked_artists[i])
                similar_artists = sp.artist_related_artists(liked_artists[i])['artists']
                if len(similar_artists) > 10:
                    similar_artists = similar_artists[:10]
                for j in range(len(similar_artists)):
                    if similar_artists[j]['id'] not in no_recommend:
                        if similar_artists[j]['id'] not in recommend_artists:
                            recommend_artists[similar_artists[j]['id']] = (20-j) * (20-i)
                        else:
                            recommend_artists[similar_artists[j]['id']] += (20-i) * (20-j)
        output = _get_top_in_dict(sp, recommend_artists)
    return output

def unlike_artist(request, id: str, like: bool):
    base = request.build_absolute_uri().split('topArtists')[0]
    token = '{}topArtists/?{}'.format(base, request.GET.urlencode())
    reader = Path('./discoverify/data/credentials.txt').open('r')
    read = reader.read().split('\n')
    reader.close()
    oauth = SpotifyOAuth(client_id = read[0], client_secret = read[1], redirect_uri = base + 'topArtists/', scope=scope, cache_path=".cache-")
    code = oauth.parse_response_code(token)
    token_info = oauth.get_access_token(code)
    if token_info:
        sp = spotipy.Spotify(auth = token_info['access_token'])
        user = sp.current_user()
        connection = sqlite3.connect('./discoverify/user_info.db')
        cursor = connection.execute('''
                                SELECT *
                                FROM user_info
                                WHERE user_id = ?;''', (user['id'],))
        info = cursor.fetchone()
        cursor.close()
        artists = info[1] if like else info[2]
        split = artists.split(id + ',')
        if like:
            connection.execute('''
                               UPDATE user_info
                               SET liked_artists = ?
                               WHERE user_id = ?;
                               ''', (split[0] + split[1], user['id']))
        else:
            connection.execute('''
                               UPDATE user_info
                               SET disliked_artists = ?
                               WHERE user_id = ?;
                               ''', (split[0] + split[1], user['id']))
        connection.commit()
        connection.close()

def like_artist(request, id: str, like: bool):
    base = request.build_absolute_uri().split('topArtists')[0]
    token = '{}topArtists/?{}'.format(base, request.GET.urlencode())
    reader = Path('./discoverify/data/credentials.txt').open('r')
    read = reader.read().split('\n')
    reader.close()
    oauth = SpotifyOAuth(client_id = read[0], client_secret = read[1], redirect_uri = base + 'topArtists/', scope=scope, cache_path=".cache-")
    code = oauth.parse_response_code(token)
    token_info = oauth.get_access_token(code)
    if token_info:
        sp = spotipy.Spotify(auth = token_info['access_token'])
        user = sp.current_user()
        connection = sqlite3.connect('./discoverify/user_info.db')
        cursor = connection.execute('''
                                    SELECT *
                                    FROM user_info
                                    WHERE user_id = ?;''', (user['id'],))
        info = cursor.fetchone()
        if info is None:
            if like:
                connection.execute('''
                                   INSERT INTO user_info (user_id, liked_artists, disliked_artists)
                                   VALUES (?, ?, "");
                                   ''', (user['id'], id))
                connection.commit()
            else:
                connection.execute('''
                                   INSERT INTO user_info (user_id, liked_artists, disliked_artists)
                                   VALUES (?, "", ?);
                                   ''', (user['id'], id))
                connection.commit()
        elif (like and len(info[1]) == 0) or (not like and len(info[2]) == 0):
            if like:
                connection.execute('''
                                   UPDATE user_info
                                   SET liked_artists = ?
                                   WHERE user_id = ?;
                                   ''', (id, user['id']))
                connection.commit()
            else:
                connection.execute('''
                                   UPDATE user_info
                                   SET disliked_artists = ?
                                   WHERE user_id = ?;
                                   ''', (id, user['id']))
                connection.commit()
        else:
            if like:
                new_artists = info[1] + ',' + id
                print(new_artists)
                connection.execute('''
                                   UPDATE user_info
                                   SET liked_artists = ?
                                   WHERE user_id = ?;
                                   ''', (new_artists, user['id']))
                connection.commit()
            else:
                new_artists = info[2] + ',' + id
                print(new_artists)
                connection.execute('''
                                   UPDATE user_info
                                   SET disliked_artists = ?
                                   WHERE user_id = ?;
                                   ''', (new_artists, user['id']))
                connection.commit()
        cursor.close()
        connection.close()
        
def get_liked_artists(request, like: bool) -> list[RecommendArtist]:
    base = request.build_absolute_uri().split('topArtists')[0]
    token = '{}topArtists/?{}'.format(base, request.GET.urlencode())
    reader = Path('./discoverify/data/credentials.txt').open('r')
    read = reader.read().split('\n')
    reader.close()
    oauth = SpotifyOAuth(client_id = read[0], client_secret = read[1], redirect_uri = base + 'topArtists/', scope=scope, cache_path=".cache-")
    code = oauth.parse_response_code(token)
    token_info = oauth.get_access_token(code)
    output = []
    if token_info:
        sp = spotipy.Spotify(auth = token_info['access_token'])
        user = sp.current_user()
        connection = sqlite3.connect('./discoverify/user_info.db')
        cursor = None
        if like:
            cursor = connection.execute('''
                                        SELECT liked_artists
                                        FROM user_info
                                        WHERE user_id = ?
                                        ''', (user['id'],))
        else:
            cursor = connection.execute('''
                                        SELECT disliked_artists
                                        FROM user_info
                                        WHERE user_id = ?
                                        ''', (user['id'],))
        artists = cursor.fetchone()
        cursor.close()
        if artists is not None:
            split = artists[0].split(',')
            for artist in split:
                info = sp.artist(artist)
                output.append(RecommendArtist(info['name'], info['images'][0]['url'], artist))
        connection.close()
    return output

def create_recommended_playlist(request) -> list[RecommendArtist]:
    base = request.build_absolute_uri().split('topArtists')[0]
    token = '{}topArtists/?{}'.format(base, request.GET.urlencode())
    reader = Path('./discoverify/data/credentials.txt').open('r')
    read = reader.read().split('\n')
    reader.close()
    oauth = SpotifyOAuth(client_id = read[0], client_secret = read[1], redirect_uri = base + 'topArtists/', scope=scope, cache_path=".cache-")
    code = oauth.parse_response_code(token)
    token_info = oauth.get_access_token(code)
    output = recommend_artists(request)
    if token_info:
        sp = spotipy.Spotify(auth = token_info['access_token'])
        user = sp.current_user()
        playlist = sp.user_playlist_create(user['id'], 'Discoverify Recommended Artists', public=False)
        id = playlist['uri'].split(':')[2]
        tracks = []
        for artist in output:
            top_tracks = sp.artist_top_tracks(artist.id)['tracks']
            for i in range(5):
                tracks.append(top_tracks[i]['uri'])
        sp.playlist_add_items(id, tracks)
    return output