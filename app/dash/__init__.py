from flask import Blueprint

bp = Blueprint('dash', __name__)

from app.dash import routes