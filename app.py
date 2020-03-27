import json
from flask import Flask, request, redirect, url_for, flash, abort

app = Flask(__name__)

@app.route('/')
def index():
    return 'hello world!'

if __name__ == '__main__':
    app.run()