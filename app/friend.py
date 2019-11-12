import functools
import requests
import math

from flask import (
    Blueprint, flash, g, redirect, render_template, request, session, url_for, jsonify
)
from more_itertools import peekable

from app.db import get_db
from app.auth import login_required

bp = Blueprint('friend', __name__)

@bp.route('/friends')
@login_required
def friends():
    # lists for storing friends ('following' and 'followers')
    following = []
    followers = []
    # query database for 'following'
    db = get_db()
    cursor = db.cursor(buffered=True)
    cursor.execute(
        "SELECT username FROM friend LEFT JOIN user ON friend_id = user.id " 
        "WHERE user_id = %s",
        (g.user[0],)
    )
    for result in cursor:
        following.append(result[0])
    # query database for 'followers'
    cursor.execute(
        "SELECT username FROM friend LEFT JOIN user ON user_id = user.id " 
        "WHERE friend_id = %s",
        (g.user[0],)
    )
    for result in cursor:
        followers.append(result[0])

    cursor.close()
    db.close()
    return render_template('friend/friends.html', following=following,
                            followers=followers)

@bp.route('/find', methods=['GET', 'POST'])
@login_required
def find():
    if request.method == 'POST':
        # reached via submitting a form
        query = request.form['query']
        # list for storing search results
        results = []
        # query database for username
        db = get_db()
        cursor = db.cursor()
        cursor.execute(
            "SELECT username FROM user WHERE username LIKE "
            "CONCAT('%', %s, '%') AND id != %s",
            (query, g.user[0])
        )
        for result in cursor:
            results.append(result[0])
        
        cursor.close()
        db.close()
        return render_template('friend/results.html', results=results)

    # reached via clicking a link
    return render_template('friend/find.html')

@bp.route('/add', methods=['POST'])
@login_required
def add():
    # get username
    username = request.json['username']
    # dict for storing response
    response = {}
    # get db connection and cursor
    db = get_db()
    cursor = db.cursor()
    # check whether friendship already exists
    cursor.execute(
        "SELECT * FROM friend WHERE user_id = %s AND friend_id = "
        "(SELECT id FROM user WHERE username = %s)",
        (g.user[0], username)
    )
    friendship = cursor.fetchone()

    if friendship:
        response['type'] = 'danger'
        response['message'] = 'You are already following ' + username
    
    if not response:
        # add friendship to 'friend' db
        cursor.execute(
            "INSERT INTO friend (user_id, friend_id) VALUES (%s, "
            "(SELECT id FROM user WHERE username = %s))",
            (g.user[0], username)
        )
        db.commit()
        response['type'] = 'success'
        response['message'] = 'You are now following ' + username
    
    return jsonify(response)

@bp.route('/remove', methods=['POST'])
@login_required
def remove():
    # get username
    username = request.json['username']
    # dict for storing response
    response = {}
    # get db connection and cursor
    db = get_db()
    cursor = db.cursor(buffered=True)
    # delete friendship from 'friend' db
    cursor.execute(
        "DELETE FROM friend WHERE user_id = %s AND friend_id = "
        "(SELECT id from user WHERE username = %s)",
        (g.user[0], username)
    )
    db.commit()
    friendship = cursor.fetchone()

    if friendship:
        response['type'] = 'danger'
        response['message'] = 'Failed to remove friend'
    
    if not response:
        response['type'] = 'success'
        response['message'] = 'Removed ' + username + ' from following'
    
    return jsonify(response)

@bp.route('/user/<username>', methods=['GET'])
def user(username):
    # query database for list of user's records (6 in a row)
    records = []
    row = []
    record = {}
    db = get_db()
    cursor = db.cursor(buffered=True)
    cursor.execute(
        "SELECT release_title, artist, discogs_uri, image_url " 
        "FROM record LEFT JOIN user ON user_id = user.id " 
        "WHERE username = %s",
        (username,)
    )
    i = 1
    p = peekable(cursor)
    for result in p:
        record['release_title'] = result[0]
        record['artist'] = result[1]
        record['uri'] = result[2]
        record['image_url'] = result[3]
        row.append(record)
        record = {}
        if i % 6 == 0 or p.peek(None) == None:
            records.append(row)
            row = []
        i += 1
    n_items = i - 1

    cursor.close()
    db.close()
    return render_template('friend/user.html', records=records,
                            n_items=n_items, username=username)