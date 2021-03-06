from flask import Flask, request, render_template, send_file
from urllib.request import urlopen
from mutagen.easyid3 import EasyID3, ID3
from mutagen.id3 import APIC as AlbumCover
from mutagen.id3 import USLT
from youtube_search import YoutubeSearch
from pytube import YouTube
import base64
import requests
import json
import pyrebase
from telegram import *
import moviepy.editor as mp
from os.path import join
import os
import re

firebaseConfig = { FIREBASE_CONFIG }

def generate_code():
    message = "SPOTIFY_ID:SPOTIFY_SECRET"
    messageBytes = message.encode('ascii')
    base64Bytes = base64.b64encode(messageBytes)
    return base64Bytes.decode('ascii')

def get_title(data):
    return data['name']

def get_album_art(data):
    imageUrl = data['album']['images'][0]['url']
    rawAlbumArt = urlopen(imageUrl).read()
    return rawAlbumArt

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
payload = {}

headers['Authorization'] = f"Basic {generate_code()}"
payload['grant_type'] = "client_credentials"

r = requests.post(tokenUrl, headers=headers, data=payload)
token = r.json()['access_token']
headers = { "Authorization": "Bearer " + token }

firebase = pyrebase.initialize_app(firebaseConfig)
db = firebase.database()

bot = Bot(BOT_TOKEN)

app = Flask(__name__)

@app.route('/', methods=['GET'])
def homepage():
    return render_template('home.html')

@app.route('/download/<trackId>')
def download(trackId):
    test = os.listdir('./')
    for item in test:
        if item.endswith(".mp3"):
            os.remove(os.path.join('./', item))
    
    #return trackId
    requestUrl = f"https://api.spotify.com/v1/tracks/{trackId}"
    response = requests.get(url=requestUrl, headers=headers)
    data = response.json()

    results = YoutubeSearch(f"{get_artists(data)}+{get_title(data)}+audio+only", max_results=10).to_dict()
    youtubeSongUrl = 'https://youtube.com/' + str(results[0]['url_suffix'])

    convertedFileName = f'{get_album_artists(data)}-{get_title(data)}'
    convertedFilePath = join('.',convertedFileName) + '.mp3'

    key = db.child('tracks').child(trackId).get()
    
    try:
        f = bot.getFile(key.val()['file_id'])
        f.download(convertedFilePath)
        return send_file(convertedFilePath, as_attachment = True)
    except:
        yt = YouTube(youtubeSongUrl)
        downloadedFilePath = yt.streams.get_audio_only().download(filename=convertedFileName,skip_existing=False)

        clip = mp.AudioFileClip(downloadedFilePath)
        clip.write_audiofile(convertedFilePath)

        audioFile = EasyID3(convertedFilePath)
        audioFile.delete()

        #Saving track info fetched from Spotify
        audioFile['title'] = get_title(data)
        audioFile['tracknumber'] = str(get_track_number(data))
        audioFile['artist'] = get_artists(data)
        audioFile['album'] = get_album_name(data)
        audioFile['albumartist'] = get_album_artists(data)
        audioFile['originaldate'] = str(get_release_year(data))

        audioFile.save(v2_version=3)

        #Saving AlbumArt
        audioFile = ID3(convertedFilePath)
        audioFile['APIC'] = AlbumCover(encoding=3,mime='image/jpeg',type=3,desc='Album Art',data=get_album_art(data))
        audioFile.save(v2_version=3)

        #remove unwanted YouTube downloads
        os.remove(downloadedFilePath)
        response = bot.send_audio(chat_id='@spotifydldatabase', title = get_title(data), performer = get_artists(data), audio=open(convertedFilePath, 'rb'))
        file_id = response['audio']['file_id']
        db.child('tracks').child(trackId).set({"file_id" : file_id})
        return send_file(convertedFilePath, as_attachment = True)

@app.route('/', methods=['POST'])
def getQuery():
    rawQuery = request.form['query']
    if 'open.spotify.com' not in rawQuery:
        return render_template('error.html')
    else:
        if '?' in rawQuery:
            trackId = rawQuery.split('/')[4].split('?')[0]
        else:
            trackId = rawQuery.split('/')[4]
        requestUrl = f"https://api.spotify.com/v1/tracks/{trackId}"
        response = requests.get(url=requestUrl, headers=headers)
        data = response.json()
        return render_template(
            'result.html',
            Uri = data['album']['images'][0]['url'],
            title = get_title(data),
            artists = get_artists(data),
            album = get_album_name(data),
            album_artists = get_album_artists(data),
            year = get_release_year(data),
            preview_url = data['preview_url'],
            trackId = trackId
        )

if __name__ == "__main__": 
    app.run(threaded = True)
