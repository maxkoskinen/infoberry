from flask import Blueprint

management = Blueprint('management', __name__)

from . import route