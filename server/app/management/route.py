from flask import request, jsonify, render_template, redirect, url_for
from . import management
from ..db import get_db

@management.route('/management', methods=['GET'])
def index():
    db = get_db()
    cur = db.execute('SELECT * FROM players ORDER BY id DESC')
    entries = cur.fetchall()
    players = [dict(entry) for entry in entries]
    return render_template("management.html",players=players)

@management.route('/management/<int:player_id>', methods=['POST'])
def delete_player(player_id):
    db = get_db()
    db.execute('DELETE from players WHERE id = ?', (player_id,))
    db.commit()
    return redirect(url_for('management.index'))

@management.route('/management/player/<int:player_id>', methods=['GET'])
def player_playlist(player_id):
    db = get_db()
    cur = db.execute('SELECT * FROM players WHERE id = ?', (player_id,))
    player = cur.fetchone()
    cur = db.execute('SELECT * FROM media WHERE player_id = ?', (player_id,))
    media = cur.fetchall()
    return render_template("player_playlist.html", player=player, media=media)


@management.route('/management/player/<int:player_id>/add-media', methods=['POST'])
def add_media_to_player(player_id):
    new_url = request.form['media_url']
    db = get_db()
    db.execute('INSERT INTO media (player_id, url) VALUES (?, ?)', (player_id, new_url))
    db.commit()
    return redirect(url_for('management.player_playlist', player_id=player_id))


@management.route('/management/player/<int:player_id>/update-settings', methods=['POST'])
def update_player_settings(player_id):
    on_time = request.form['on_time']
    off_time = request.form['off_time']
    switch_tab_interval = request.form['switch_tab_interval']

    db = get_db()

    if on_time:
        db.execute('UPDATE players SET on_time = ? WHERE id = ?', (on_time, player_id))

    if off_time:
        db.execute('UPDATE players SET off_time = ? WHERE id = ?', (off_time, player_id))

    if switch_tab_interval:
        db.execute('UPDATE players SET switch_tab_interval = ? WHERE id = ?', (switch_tab_interval, player_id))
    db.commit()

    return redirect(url_for('management.player_playlist', player_id=player_id))


@management.route('/management/player/<int:player_id>/remove-media/<int:media_id>', methods=['POST'])
def remove_media_from_player(player_id, media_id):
    db = get_db()
    db.execute('DELETE FROM media WHERE id = ? AND player_id = ?', (media_id, player_id))
    db.commit()
    return redirect(url_for('management.player_playlist', player_id=player_id))