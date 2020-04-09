import requests 
import json
import os

#do not push api key
api_key = os.getenv('SL_KEY')
url = "https://api.setlist.fm/rest/1.0/"

def get_artist_concerts(artist: str):
    full_url = url+'artist/'+artist+'/setlists'
    payload = {}
    headers = {
    'Accept': 'application/json',
    'x-api-key': api_key
    }
    response = requests.request("GET", full_url, headers=headers, data = payload)
    sets = json.loads(response.text)
    performances = []
    for s in sets['setlist']:
        if 'info' in s:
            performances.append([s['id'], s['info']])
        else:
            performances.append([s['id'],s['eventDate']])
    return performances

def get_event_setlist(event_id: str):
    full_url = url+'setlist/'+event_id
    payload = {}
    headers = {
    'Accept': 'application/json',
    'x-api-key': api_key
    }
    response = requests.request("GET", full_url, headers=headers, data = payload)
    setlist = json.loads(response.text)
    songs = []
    for song in setlist["sets"]["set"]:
        for s in song['song']:
            songs.append(s['name'])
    return songs


#print(get_artist_concerts("65f4f0c5-ef9e-490c-aee3-909e7ae6b2ab"))
#print(get_event_setlist("7bf052c0"))