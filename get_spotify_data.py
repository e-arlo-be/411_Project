import requests
import os
import argparse
#spotipy imports
import spotipy
import spotipy.util as util

client_id: str = os.getenv("SPOT_ID")
client_secret: str = os.getenv("SPOT_SECRET")

def login_spotify():
    url = "https://accounts.spotify.com/authorize?client_id="+client_id+"&response_type=code&redirect_uri=http://127.0.0.1:5000/spotify_callback&scope=playlist-modify-private"

    payload = {}
    headers = {
        'Authorization': 'Bearer BQDqF8SD3szUwM8aLup6tbEbImHlKPxczo2DFGUontIusvj1xmjpg-F55PsZBaTBOg2bItXt3QUBbYa1HmQ',
        'Cookie': 'inapptestgroup=; __Host-device_id=AQB3bZCwd8sniaS06zH4AEUUl4mJeVKAwFiuPF5nsvADu2YLHWrVc5e3pcR1sWHyNFyIZXIiJuSe-uN-bGDVgx_6wtkL3PIsaY4; __Secure-TPASESSION=AQBcNHmxejVVgckefZUx0zidWzfNti4uMg7Ll3m5Zh5hlc61cftd7KoOTQhnvH5Y5PWkCq7mnFXo/OaLB4cnSAI73YK2r+VioWE=; csrf_token=AQAqlAI0Z4q6Su3uGIVrjXwILKRP9wPo3VSlsg-VdmhVKKPXddZJsG-MuQ7V345zrtJdLMewKmY0jaqc'
    }
    response = requests.request("GET", url, headers=headers, data = payload)
    return response.text.encode('utf8')
def spotify_authenticate() -> str:
    data = {'grant_type': 'client_credentials'}
    url = 'https://accounts.spotify.com/api/token'
    response = requests.post(url, data=data, auth=(client_id, client_secret))
    return response.json()['access_token']

def get_track(access_token: str, song: str, artist: str) -> [str]:
    url = "https://api.spotify.com/v1/search?q="+song+"&type=track"

    payload = {}
    headers = {
    'Accept': 'application/json',
    'Authorization': 'Bearer '+access_token
    }

    response = requests.request("GET", url, headers=headers, data = payload)
    data = response.json()
    if len(data['tracks']['items']) > 0:
        for item in data['tracks']['items']:
            for track_artist in item['artists']:
                if track_artist['name'] == artist:
                    track_name = item['name']
                    track_url = item['external_urls']['spotify']
                    track_id = item['id']
                    return([track_name, track_url, track_id])
    return [song, 'no_track']


#token = spotify_authenticate()
#print(get_track(token, "Hardwired"))