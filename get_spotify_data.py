import requests
import os

client_id: str = os.getenv("SPOT_ID")
client_secret: str = os.getenv("SPOT_SECRET")
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
                    return([track_name, track_url])
    return [song, 'no_track']
#token = spotify_authenticate()
#print(get_track(token, "Hardwired"))