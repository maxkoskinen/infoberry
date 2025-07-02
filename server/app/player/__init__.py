from flask import Blueprint

player = Blueprint('player', __name__)

from . import route