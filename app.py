import json
import sqlite3

from flask_login import (
    LoginManager,
    current_user,
    login_required,
    login_user,
    logout_user,
)
from oauthlib.oauth2 import WebApplicationClient
import requests
# Internal imports
from db import init_db_command
from user import User

#spotipy imports
import spotipy
import spotipy.util as util

import os
from flask import Flask, request, redirect, url_for, render_template, session
from get_setlist_data import *
from get_spotify_data import *



# Configuration
GOOGLE_CLIENT_ID = os.environ.get("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.environ.get("GOOGLE_CLIENT_SECRET")
GOOGLE_DISCOVERY_URL = (
    "https://accounts.google.com/.well-known/openid-configuration"
)

# Flask app setup
app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY") or os.urandom(24)

# User session management setup
login_manager = LoginManager()
login_manager.init_app(app)

#Spotify Setup
SPOTIFY_API_BASE = 'https://accounts.spotify.com'
SPOTIFY_REDIRECT_URI = "https://127.0.0.1:5000/spotify/callback"
SPOT_ID = os.environ.get("SPOT_ID")
SPOT_SECRET = os.environ.get("SPOT_SECRET")
SCOPE = 'playlist-modify-private'

@login_manager.unauthorized_handler
def unauthorized():
    return "You must be logged in to access this content.", 403


# Naive database setup
try:
    init_db_command()
except sqlite3.OperationalError:
    # Assume it's already been created
    pass

# OAuth2 client setup
client = WebApplicationClient(GOOGLE_CLIENT_ID)

# Flask-Login helper to retrieve a user from our db
@login_manager.user_loader
def load_user(user_id):
    return User.get(user_id)


@app.route("/", methods=["GET","POST"])
def index():
    if current_user.is_authenticated:
        return redirect('homepage')
    else:
        return render_template('index.html')


@app.route("/login")
def login():
    google_provider_cfg = get_google_provider_cfg()
    authorization_endpoint = google_provider_cfg["authorization_endpoint"]
    request_uri = client.prepare_request_uri(
        authorization_endpoint,
        redirect_uri=request.base_url + "/callback",
        scope=["openid", "email", "profile"],
    )
    return redirect(request_uri)


@app.route("/login/callback")
def callback():
    # Get authorization code Google sent back to you
    code = request.args.get("code")

    # Find out what URL to hit to get tokens that allow you to ask for
    # things on behalf of a user
    google_provider_cfg = get_google_provider_cfg()
    token_endpoint = google_provider_cfg["token_endpoint"]

    # Prepare and send request to get tokens! Yay tokens!
    token_url, headers, body = client.prepare_token_request(
        token_endpoint,
        authorization_response=request.url,
        redirect_url=request.base_url,
        code=code,
    )
    token_response = requests.post(
        token_url,
        headers=headers,
        data=body,
        auth=(GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET),
    )

    # Parse the tokens!
    client.parse_request_body_response(json.dumps(token_response.json()))

    # Now that we have tokens (yay) let's find and hit URL
    # from Google that gives you user's profile information,
    # including their Google Profile Image and Email
    userinfo_endpoint = google_provider_cfg["userinfo_endpoint"]
    uri, headers, body = client.add_token(userinfo_endpoint)
    userinfo_response = requests.get(uri, headers=headers, data=body)

    # We want to make sure their email is verified.
    # The user authenticated with Google, authorized our
    # app, and now we've verified their email through Google!
    if userinfo_response.json().get("email_verified"):
        unique_id = userinfo_response.json()["sub"]
        users_email = userinfo_response.json()["email"]
        picture = userinfo_response.json()["picture"]
        users_name = userinfo_response.json()["given_name"]
    else:
        return "User email not available or not verified by Google.", 400

    # Create a user in our db with the information provided
    # by Google
    user = User(
        id_=unique_id, name=users_name, email=users_email, profile_pic=picture
    )

    # Doesn't exist? Add to database
    if not User.get(unique_id):
        User.create(unique_id, users_name, users_email, picture)

    # Begin user session by logging the user in
    login_user(user)

    # Send user back to homepage
    return redirect(url_for("index"))


@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("index"))


def get_google_provider_cfg():
    return requests.get(GOOGLE_DISCOVERY_URL).json()

@app.route("/spotify/callback")
def spot_callback():
    # Don't reuse a SpotifyOAuth object because they store token info and you could leak user tokens if you reuse a SpotifyOAuth object
    sp_oauth = spotipy.oauth2.SpotifyOAuth(client_id = SPOT_ID, client_secret = SPOT_SECRET, redirect_uri = SPOTIFY_REDIRECT_URI, scope = SCOPE)
    code = request.args.get('code')
    token_info = sp_oauth.get_access_token(code, check_cache=False)
    #print(token_info)
    # Saving the access token along with all other token related info
    session["token_info"] = token_info
    sp = spotipy.Spotify(auth=session.get('token_info').get('access_token'))
    user = sp.current_user()['id']
    playlist = sp.user_playlist_create(user, session['event_id'], public=False)
    playlist_id = playlist['id']
    session['playlist_url'] = playlist['external_urls']['spotify']
    sp.user_playlist_add_tracks(user, playlist_id, session['song_ids'])
    return redirect(url_for("setlist"))

@app.route("/spotify")
def spot_log():
    sp_oauth = spotipy.oauth2.SpotifyOAuth(client_id = SPOT_ID, client_secret = SPOT_SECRET, redirect_uri = SPOTIFY_REDIRECT_URI, scope = SCOPE)
    auth_url = sp_oauth.get_authorize_url()
    print(auth_url)
    return redirect(auth_url)

@app.route('/homepage', methods=["GET","POST"])
def indexhome():
    if request.method == 'POST':
        session['artist_id'] = request.form['artist']
        #print("yo")
        return redirect('show')
    return render_template('indexhome.html', name =  current_user.name, email = current_user.email, pic = current_user.profile_pic)

@app.route('/show', methods=['GET','POST'])
def show():
    shows = [[None, None]]
    if 'artist_id' in session:
            show_list = get_artist_concerts(session['artist_id'])
            shows = show_list[0]
    if request.method == 'POST':
        session['event_id'] = request.form['shows']
        session['artist'] = show_list[1]
        return redirect('setlist')
    return render_template('shows.html', shows=shows)

@app.route('/setlist', methods=['GET','POST'])
def setlist():
    if 'event_id' in session:
        playlist = 'No playlist created yet'
        playlist_url = '/setlist'
        if 'playlist_url' in session:
            playlist_url = session['playlist_url']
            playlist = 'See your created playlist!'
        songs = get_event_setlist(session['event_id'])
        access_token = spotify_authenticate()
        song_data = []
        song_ids = []
        for song in songs:
            song_data.append(get_track(access_token, song, session['artist']))
        for song in song_data:
            if len(song) == 3:
                song_ids.append(song[2])
        session['song_ids'] = song_ids
        return render_template('setlist.html', songs=song_data, playlist = playlist, playlist_url = playlist_url)
    return 'Please fill out all previous forms'

@app.route('/no_track')
def no_track():
    return render_template('no_track.html')



if __name__ == '__main__':
    app.run(ssl_context="adhoc")
