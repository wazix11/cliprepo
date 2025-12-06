import os, secrets, requests
from datetime import datetime, timezone, timedelta
from urllib.parse import urlencode
from dotenv import load_dotenv
from flask import redirect, url_for, flash, abort, session, request
from flask_login import login_user, logout_user, current_user
from app import db
from app.auth import bp
from app.models import User
from app.auth.oauth_utils import (
    refresh_user_access_token,
    ExpiredAccessTokenError,
    require_scopes
)

load_dotenv(override=True)
TWITCH_CLIENT_ID = os.environ.get('TWITCH_CLIENT_ID')
TWITCH_CLIENT_SECRET = os.environ.get('TWITCH_CLIENT_SECRET')
TWITCH_OAUTH_REDIRECT_URI = os.environ.get('TWITCH_OAUTH_REDIRECT_URI')
TWITCH_CLIENT_ACCESS_TOKEN = ''
TWITCH_AUTHORIZE_URL = 'https://id.twitch.tv/oauth2/authorize'
TWITCH_SCOPES = []
TWITCH_TOKEN_URL = 'https://id.twitch.tv/oauth2/token'
TWITCH_USERINFO_URL = 'https://api.twitch.tv/helix/users'
TWITCH_CLIP_URL = 'https://api.twitch.tv/helix/clips'
TWITCH_VALIDATE_URL = 'https://id.twitch.tv/oauth2/validate'
TWITCH_REVOKE_URL = 'https://id.twitch.tv/oauth2/revoke'
SUPERADMIN_NAMES = os.environ.get('SUPERADMIN_NAMES').lower().split(',')

@bp.before_app_request
def check_user_token():
    """Check and refresh users access token before each request."""
    if request.endpoint and (
        request.endpoint.startswith('static') or
        request.endpoint in ['auth.logout', 'auth.oauth2_authorize', 'auth.oauth2_callback']
    ):
        return
    
    if not current_user.is_anonymous:
        try:
            refresh_user_access_token(current_user)
        except ExpiredAccessTokenError:
            logout_user()
            flash('Your session has expired. Please log in again.', 'warning')
            return redirect(url_for('auth.oauth2_authorize'))

@bp.route('/logout')
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('main.index'))

@bp.route('/authorize')
def oauth2_authorize():
    if not current_user.is_anonymous:
        return redirect(url_for('main.index'))
    
    # generate a random string for the state parameter
    session['oauth2_state'] = secrets.token_urlsafe(16)

    # create a query string with all the OAuth2 parameters
    qs = urlencode({
        'client_id': TWITCH_CLIENT_ID,
        'redirect_uri': f'{TWITCH_OAUTH_REDIRECT_URI}/callback',
        'response_type': 'code',
        'scope': ' '.join(TWITCH_SCOPES),
        'state': session['oauth2_state'],
    })

    # redirect the user to the OAuth2 provider authorization URL
    return redirect(TWITCH_AUTHORIZE_URL + '?' + qs)

@bp.route('/callback')
def oauth2_callback():
    if not current_user.is_anonymous:
        return redirect(url_for('main.index'))

    # if there was an authentication error, flash the error messages and exit
    if 'error' in request.args:
        for k, v in request.args.items():
            if k.startswith('error'):
                flash(f'{k}: {v}')
        return redirect(url_for('main.index'))

    # make sure that the state parameter matches the one we created in the
    # authorization request
    if request.args['state'] != session.get('oauth2_state'):
        abort(401)

    # make sure that the authorization code is present
    if 'code' not in request.args:
        abort(401)

    # exchange the authorization code for an access token
    response = requests.post(TWITCH_TOKEN_URL, data={
        'client_id': TWITCH_CLIENT_ID,
        'client_secret': TWITCH_CLIENT_SECRET,
        'code': request.args['code'],
        'grant_type': 'authorization_code',
        'redirect_uri': f'{TWITCH_OAUTH_REDIRECT_URI}/callback',
    }, headers={'Accept': 'application/json'})

    if response.status_code != 200:
        abort(401)

    token_data = response.json()
    oauth2_token = token_data.get('access_token')
    user_refresh_token = token_data.get('refresh_token')
    expires_in = token_data.get('expires_in', 3600)
    token_scope = token_data.get('scope', '').replace(',', ' ')

    if not oauth2_token:
        abort(401)

    # use the access token to get the user's info
    response = requests.get(TWITCH_USERINFO_URL, headers={
        'Authorization': 'Bearer ' + oauth2_token,
        'Accept': 'application/json',
        'Client-Id': TWITCH_CLIENT_ID
    })

    if response.status_code != 200:
        abort(401)
    
    data = response.json()['data'][0]
    user_id = data['id']
    user_login = data['login']
    user_display_name = data['display_name']
    user_profile_image_url = data['profile_image_url']

    now = datetime.now(timezone.utc)
    token_expires_at = now + timedelta(seconds=expires_in)
    
    # find or create the user in the database
    user = db.session.scalar(db.select(User).where(User.twitch_id == user_id))

    if user is None:
        rank_id = 1
        if user_display_name.lower() in SUPERADMIN_NAMES:
            rank_id = 4
        user = User(
            twitch_id=user_id, 
            login=user_login, 
            display_name=user_display_name, 
            profile_image_url=user_profile_image_url,
            access_token=oauth2_token,
            refresh_token=user_refresh_token,
            expires_at=token_expires_at,
            last_verified=now,
            token_scope=token_scope,
            rank_id=rank_id
        )
        db.session.add(user)
    else:
        user.twitch_id = user_id
        user.login = user_login
        user.display_name = user_display_name
        user.profile_image_url = user_profile_image_url
        user.access_token = oauth2_token
        user.refresh_token = user_refresh_token
        user.expires_at = token_expires_at
        user.last_verified = now
        user.token_scope = token_scope
        
    db.session.commit()
    # log the user in
    login_user(user)
    return redirect(url_for('main.index'))