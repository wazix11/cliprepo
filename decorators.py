from functools import wraps
from flask import abort, request
from flask_login import current_user
from werkzeug.security import check_password_hash
from app.models import ApiKey
from app import db

def rank_required(*ranks):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if current_user.rank.name not in ranks:
                abort(403)
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def require_api_key(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        auth_header = request.headers.get('Authorization')

        if not auth_header or not auth_header.startswith('Bearer '):
            return {'error': 'Unauthorized', 'message': 'Invalid or missing API key'}, 401
        
        provided_key = auth_header.split(' ')[1]
        provided_key_lookup_id = provided_key.split('_')[1]  # Extract the lookup ID part
        provided_key_hash = provided_key.split('_')[-1]  # Extract the actual key part
        api_key = ApiKey.query.filter_by(key_id=provided_key_lookup_id).first()
        if not api_key or not check_password_hash(api_key.key_hash, provided_key_hash):
            return {'error': 'Unauthorized', 'message': 'Invalid API key'}, 401
        api_key.uses += 1
        db.session.commit()
        return f(*args, **kwargs)
    return decorated_function