import os, secrets, requests
from urllib.parse import urlencode
from dotenv import load_dotenv
from flask import redirect, url_for, flash, abort, session, request
from flask_login import login_user, logout_user, current_user
from app import db
from app.auth import bp
from app.models import User

load_dotenv()
TWITCH_CLIENT_ID = os.environ.get('TWITCH_CLIENT_ID')
TWITCH_CLIENT_SECRET = os.environ.get('TWITCH_CLIENT_SECRET')
TWITCH_CLIENT_ACCESS_TOKEN = ''
TWITCH_AUTHORIZE_URL = 'https://id.twitch.tv/oauth2/authorize'
TWITCH_SCOPES = []
TWITCH_TOKEN_URL = 'https://id.twitch.tv/oauth2/token'
TWITCH_USERINFO_URL = 'https://api.twitch.tv/helix/users'
TWITCH_CLIP_URL = 'https://api.twitch.tv/helix/clips'
TWITCH_VALIDATE_URL = 'https://id.twitch.tv/oauth2/validate'
TWITCH_REVOKE_URL = 'https://id.twitch.tv/oauth2/revoke'
SUPERADMIN_NAMES = os.environ.get('SUPERADMIN_NAMES').lower().split(',')

@bp.route('/logout')
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('main.index'))

def validate_access_token(access_token):
    headers = {
        'Authorization': f'OAuth {access_token}'
    }
    response = requests.get(TWITCH_VALIDATE_URL, headers=headers)
    print(response.json())
    return response.json()

def refresh_access_token(refresh_token):
    params = {
        'client_id': TWITCH_CLIENT_ID,
        'client_secret': TWITCH_CLIENT_SECRET,
        'grant_type': 'refresh_token',
        'refresh_token': refresh_token
    }
    response = requests.post(TWITCH_TOKEN_URL, data=params)
    return response.json()

def revoke_access_token(access_token):
    params = {
        'client_id': TWITCH_CLIENT_ID,
        'token': access_token
    } 
    headers = {'Content-Type': 'application/x-www-form-urlencoded'}

    response = requests.post(TWITCH_REVOKE_URL, headers=headers, data=params)
    return response.json()

# Function to periodically check and update the access token
# TODO needs a bunch of work, especially on error responses
# also just doesn't actually work, this doesn't seem to run within the app context
def check_access_token():
    print(current_user)
    access_token = current_user.access_token
    if access_token:
        validation_response = validate_access_token(access_token)
        if 'status' in validation_response and validation_response['status'] == 401:
            # Access token is expired, refresh it
            refresh_token = current_user.refresh_token
            new_token_response = refresh_access_token(refresh_token)
            current_user.access_token = new_token_response.get('access_token')
            current_user.refresh_token = new_token_response.get('refresh_token')
            # Update the user's access token in the database
            db.session.commit()

def get_client_access_token():
    pass

@bp.route('/authorize')
def oauth2_authorize():
    if not current_user.is_anonymous:
        return redirect(url_for('main.index'))
    
    # generate a random string for the state parameter
    session['oauth2_state'] = secrets.token_urlsafe(16)

    # create a query string with all the OAuth2 parameters
    qs = urlencode({
        'client_id': TWITCH_CLIENT_ID,
        'redirect_uri': url_for('auth.oauth2_callback',
                                _external=True),
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
        print('State parameter mismatch')
        abort(401)

    # make sure that the authorization code is present
    if 'code' not in request.args:
        print('Authorization code not present')
        abort(401)

    # exchange the authorization code for an access token
    response = requests.post(TWITCH_TOKEN_URL, data={
        'client_id': TWITCH_CLIENT_ID,
        'client_secret': TWITCH_CLIENT_SECRET,
        'code': request.args['code'],
        'grant_type': 'authorization_code',
        'redirect_uri': url_for('auth.oauth2_callback',
                                _external=True),
    }, headers={'Accept': 'application/json'})
    if response.status_code != 200:
        print('Access token request failed')
        abort(401)
    oauth2_token = response.json().get('access_token')
    user_refresh_token = response.json().get('refresh_token')
    if not oauth2_token:
        print('Access token request failed 2')
        abort(401)

    # use the access token to get the user's info
    response = requests.get(TWITCH_USERINFO_URL, headers={
        'Authorization': 'Bearer ' + oauth2_token,
        'Accept': 'application/json',
        'Client-Id': TWITCH_CLIENT_ID
    })
    if response.status_code != 200:
        print('Unable to retrieve user info')
        abort(401)
    
    data = response.json()
    
    user_id = data['data'][0]['id']
    user_login = data['data'][0]['login']
    user_display_name = data['data'][0]['display_name']
    user_profile_image_url = data['data'][0]['profile_image_url']
    
    # find or create the user in the database
    user = db.session.scalar(db.select(User).where(User.twitch_id == user_id))
    if user is None:
        rank_id = 1
        if user_display_name.lower() in SUPERADMIN_NAMES:
            rank_id = 4
        user = User(twitch_id=user_id, 
                    login=user_login, 
                    display_name=user_display_name, 
                    profile_image_url=user_profile_image_url,
                    access_token=oauth2_token,
                    refresh_token=user_refresh_token,
                    rank_id=rank_id)
        db.session.add(user)
        db.session.commit()
    else:
        user.twitch_id = user_id
        user.login = user_login
        user.display_name = user_display_name
        user.profile_image_url = user_profile_image_url
        user.access_token = oauth2_token
        user.refresh_token = user_refresh_token
        db.session.commit()

    # log the user in
    login_user(user)
    return redirect(url_for('main.index'))