import os
from flask import Flask, request, redirect, url_for, render_template, session
from get_setlist_data import *

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
            shows = get_artist_concerts(session['artist_id'])
    if request.method == 'POST':
        session['event_id'] = request.form['shows']
        return redirect('setlist')
    return render_template('shows.html', shows=shows)

@app.route('/setlist')
def setlist():
    if 'event_id' in session:
        songs = get_event_setlist(session['event_id'])
        return render_template('setlist.html', songs=songs)
    return 'Please fill out all previous forms'
if __name__ == '__main__':
    app.run()