from functools import wraps
from flask import abort
from flask_login import current_user

def rank_required(*ranks):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if current_user.rank.name not in ranks:
                abort(403)
            return f(*args, **kwargs)
        return decorated_function
    return decorator