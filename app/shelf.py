import functools
import requests
import math

from flask import (
    Blueprint, flash, g, redirect, render_template, request, session, url_for, jsonify
)
from more_itertools import peekable

from app.db import get_db
from app.auth import login_required
from instance.config import API_KEY, API_SECRET

bp = Blueprint('shelf', __name__, url_prefix='/shelf')

@bp.route('/')
@login_required
def index():
    # query database for list of user's records (6 in a row)
    records = []
    row = []
    record = {}
    db = get_db()
    cursor = db.cursor(buffered=True)
    cursor.execute(
        "SELECT * FROM record WHERE user_id = %s",
        (g.user[0],)
    )
    i = 1
    p = peekable(cursor)
    for result in p:
        record['release_title'] = result[2]
        record['artist'] = result[3]
        record['uri'] = result[4]
        record['image_url'] = result[5]
        row.append(record)
        record = {}
        if i % 6 == 0 or p.peek(None) == None:
            records.append(row)
            row = []
        i += 1
    n_items = i - 1

    cursor.close()
    db.close()
    return render_template('shelf/index.html', records=records,
                            n_items=n_items)

@bp.route('/search', methods=['GET', 'POST'])
def search():
    if request.method == 'POST' or request.args:
        # reached via submitting search form or pagination GET request
        if request.method == 'POST':
            # get parameters from form
            query = request.form['query']
            page = request.form['page']
            limit = request.form['limit']
        else:
            # get parameters from URL
            query = request.args['query']
            page = request.args['page']
            limit = request.args['limit']
        # list and dict for storing records (6 in a row)/record info
        records = []
        row = []
        record = {}
        # make API request
        URL = 'https://api.discogs.com/database/search'
        PARAMS = {
            'query': query,
            'key': API_KEY,
            'secret': API_SECRET,
            'format': 'vinyl',
            'type': 'release',
            'page': page,
            'per_page': limit
        }
        response = requests.get(url=URL, params = PARAMS)
        # deserialize response
        data = response.json()
        n_items = data['pagination']['items']
        max_pages = math.ceil(int(n_items) / int(limit))
        results = data.get('results', [])
        i = 1
        for result in results:
            title = result.get('title', 'Not found-Not found')
            record['release_title'] = title.split('-')[1]
            record['artist'] = title.split('-')[0]
            record['uri'] = result.get('uri')
            record['image_url'] = result.get('cover_image', 'Not found')
            row.append(record)
            record = {}
            if i % 6 == 0 or i == len(results):
                records.append(row)
                row = []
            i += 1
        return render_template('shelf/results.html', records=records, 
                                n_items=n_items, query=query,
                                page=page, max_pages=max_pages,
                                limit=limit)
    # reached via clicking a link
    return render_template('shelf/search.html')

@bp.route('/add', methods=['POST'])
@login_required
def add():
    release_title = request.json['release_title']
    artist = request.json['artist']
    uri = request.json['uri']
    image_url = request.json['image_url']
    response = {}

    db = get_db()
    cursor = db.cursor(buffered=True)
    cursor.execute(
        "SELECT * FROM record WHERE user_id = %s AND discogs_uri = %s",
        (g.user[0], uri)
    )
    record = cursor.fetchone()

    if record:
        response['type'] = 'danger'
        response['message'] = (release_title + ' by ' + artist + ' is ' +
                              'already in your collection')
    
    if not response:
        cursor.execute(
            "INSERT INTO record (user_id, release_title, artist, discogs_uri"
            ", image_url) VALUES (%s, %s, %s, %s, %s)",
            (g.user[0], release_title, artist, uri, image_url)
        )
        db.commit()
        response['type'] = 'success'
        response['message'] = (release_title + ' by ' + artist + ' added ' +
                               'to your collection')
    
    cursor.close()
    db.close()
    return jsonify(response)

@bp.route('/remove', methods=['POST'])
@login_required
def remove():
    uri = request.json['uri']
    response = {}

    db = get_db()
    cursor = db.cursor(buffered=True)
    cursor.execute(
        "DELETE FROM record WHERE user_id = %s AND discogs_uri = %s",
        (g.user[0], uri)
    )
    db.commit()
    record = cursor.fetchone()

    if record:
        response['type'] = 'danger'
        response['message'] = 'Failed to remove record'
    
    if not response:
        response['type'] = 'success'
        response['message'] = 'Record removed successfully'
    
    cursor.close()
    db.close()
    return jsonify(response)





