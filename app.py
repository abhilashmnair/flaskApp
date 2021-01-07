from flask import Flask, request, render_template, send_file
#from urllib.request import urlopen
#from mutagen.id3 import APIC as AlbumCover
import base64
import requests
import json

def search_song(q):
    if 'open.spotify.com' in q:
        return q.split('/')[4]
    else:
        query = '+'.join(str(val) for val in q.split(' '))
        requestUrl = f"https://api.spotify.com/v1/search?q={query}&type=track,artist,album"
        response = requests.get(url=requestUrl, headers=headers)
        data = response.json()
        try:
            return data['tracks']['items'][0]['id']
        except:
            return None

def generate_code():
    message = '6923be29233a454f83f3db90b3172606:c0ec28811f0843d9aeea0a890cca3af2'
    messageBytes = message.encode('ascii')
    base64Bytes = base64.b64encode(messageBytes)
    return base64Bytes.decode('ascii')

def get_title(data):
    return data['name']

def get_album_art(data):
    imageUrl = data['album']['images'][0]['url']
    return imageUrl

def get_artists(data):
    artists = []
    for item in data['artists']:
        artists.append(item['name'])
    return ', '.join(str(val) for val in artists)

def get_album_name(data):
    return data['album']['name']

def get_track_number(data):
    return data['track_number']

def get_disc_number(data):
    return data['disc_number']

def get_release_year(data):
    date = data['album']['release_date']
    year = date.split('-')
    return year[0]

def get_album_artists(data):
    album_artists = []
    for item in data['album']['artists']:
        album_artists.append(item['name'])
    return ', '.join(str(val) for val in album_artists)

tokenUrl = "https://accounts.spotify.com/api/token"
headers = {}
data = {}

headers['Authorization'] = f"Basic {generate_code()}"
data['grant_type'] = "client_credentials"

r = requests.post(tokenUrl, headers=headers, data=data)
token = r.json()['access_token']
headers = { "Authorization": "Bearer " + token }

app = Flask(__name__)

@app.route('/', methods=['GET'])
def homepage():
    return render_template('home.html')

@app.route('/download')
def download():
    print('Testing...')
    return None

@app.route('/', methods=['POST'])
def getQuery():
    text = request.form['query']
    trackId = search_song(text)
    requestUrl = f"https://api.spotify.com/v1/tracks/{trackId}"
    response = requests.get(url=requestUrl, headers=headers)
    if response.ok:
        data = response.json()
        return render_template(
            'result.html',
            Uri = get_album_art(data),
            title = get_title(data),
            artists = get_artists(data),
            album = get_album_name(data),
            album_artists = get_album_artists(data),
            year = get_release_year(data),
            preview_url = data['preview_url']
        )
    else:
        return render_template('error.html')

if __name__ == '__main__':
    app.run(debug = True)