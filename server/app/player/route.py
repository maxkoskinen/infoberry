from flask import request, jsonify
from datetime import datetime
from . import player
from ..db import get_db

@player.route('/')
def index():
    return "Raspi Info screen API"

@player.route('/register', methods=['POST'])
def add_player():
    name = request.json.get('name')
    description = request.json.get('description')
    serial = request.json.get('serial')
    print(serial)
    if not name or not description or not serial:
        return jsonify({"error": "Name, description, and IP are required"}), 400

    db = get_db()

    # check if player already exists
    cur = db.execute('SELECT * FROM players WHERE (serial = ?)', (serial,))
    existing_player = cur.fetchone()

    if existing_player:
        return jsonify({"error": "Player already exists"}), 201

    db.execute('INSERT INTO players (name, description, serial) VALUES (?, ?, ?)',
               (name, description, serial))
    db.commit()
    return jsonify({"message": "New player registered successfully"}), 201


@player.route('/playlist', methods=['GET'])
def get_playlist():
    serial = request.json.get('serial')
    if not serial:
        return jsonify({"error: no serial"}), 400

    db = get_db()
    cur = db.execute('SELECT * FROM players WHERE (serial = ?)', (serial,))
    player = cur.fetchone()

    if not player:
        return jsonify({"error: no such player"}), 404

    cur = db.execute('SELECT (url) FROM media WHERE player_id = ?', (player['id'],))
    media = cur.fetchall()
    media = [entry['url'] for entry in media]
    print(media)
    return jsonify(media), 200


@player.route('/ping', methods=['POST'])
def client_ping():
    serial = request.json.get('serial')
    if not serial:
        return jsonify({"error": "Bad Request"}), 400
    
    db = get_db()

    current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    cur = db.execute('UPDATE players set last_ping = ? WHERE serial = ?', (current_time, serial))
    db.commit()

    return jsonify({"message": "Ping Received"}), 200

@player.route('/settings', methods=['GET'])
def get_settings():
    serial = request.json.get('serial')

    if not serial:
        return jsonify({"error: no serial"}), 400
    
    db = get_db()

    cur = db.execute('SELECT on_time, off_time, switch_tab_interval FROM players WHERE (serial = ?)', (serial,))
    settings = cur.fetchone()
    
    return jsonify(dict(settings)), 200

    
