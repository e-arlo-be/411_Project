import os
from flask import Flask, request, redirect, url_for, render_template, session
from get_setlist_data import *
from get_spotify_data import *

app = Flask(__name__)
app.secret_key = os.urandom(24)

@app.route('/', methods=["GET","POST"])
def index():
    if request.method == 'POST':
        session['artist_id'] = request.form['artist']
        return redirect('show')
    return render_template('index.html')

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

@app.route('/setlist')
def setlist():
    if 'event_id' in session:
        songs = get_event_setlist(session['event_id'])
        access_token = spotify_authenticate()
        song_data = []
        for song in songs:
            song_data.append(get_track(access_token, song, session['artist']))

        return render_template('setlist.html', songs=song_data)
    return 'Please fill out all previous forms'

@app.route('/no_track')
def no_track():
    return render_template('no_track.html')
if __name__ == '__main__':
    app.run()