import os, secrets, requests
from urllib.parse import urlencode
from dotenv import load_dotenv
from datetime import datetime, timezone
from flask import render_template, redirect, url_for, flash, abort, session, request
from flask_login import login_user, logout_user, login_required, current_user
from app import db, scheduler
from app.auth import bp
from app.models import User, Clip

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

@bp.route('/logout')
def logout():
    logout_user()
    if scheduler.running:
        scheduler.shutdown()
    flash('You have been logged out.', 'info')
    return redirect(url_for('main.index'))

def update_client_credentials():
    params = {
        'client_id': TWITCH_CLIENT_ID,
        'client_secret': TWITCH_CLIENT_SECRET,
        'grant_type': 'client_credentials'
    }
    response = requests.post(TWITCH_TOKEN_URL, data=params)
    data = response.json()
    global TWITCH_CLIENT_ACCESS_TOKEN
    TWITCH_CLIENT_ACCESS_TOKEN = data['access_token']

# TODO: add error checking to make sure the access token is valid and get clips from AlveusSanctuary
@bp.route('/get_clips')
@login_required
def get_clips():
    if current_user.rank.name in ['SUPERADMIN', 'ADMIN', 'MODERATOR']:
        if TWITCH_CLIENT_ACCESS_TOKEN == '':
            update_client_credentials()
        print(TWITCH_CLIENT_ACCESS_TOKEN)
        headers = {
            'Authorization': f'Bearer {TWITCH_CLIENT_ACCESS_TOKEN}',
            'Client-Id': TWITCH_CLIENT_ID
        }
        qs = urlencode({
            'broadcaster_id': 636587384,
            'first': 100
        })
        response = requests.get(TWITCH_CLIP_URL + '?' + qs, headers=headers)
        data = response.json()
        clips_to_add = []
        for clip in data['data']:
            existing_clip = Clip.query.filter_by(twitch_id=clip['id']).first()

            if existing_clip:
                # Update existing clip fields
                existing_clip.url = clip['url']
                existing_clip.embed_url = clip['embed_url']
                existing_clip.broadcaster_id = clip['broadcaster_id']
                existing_clip.broadcaster_name = clip['broadcaster_name']
                existing_clip.creator_id = clip['creator_id']
                existing_clip.creator_name = clip['creator_name']
                existing_clip.title = clip['title']
                existing_clip.view_count = clip['view_count']
                existing_clip.created_at = clip['created_at']
                existing_clip.thumbnail_url = clip['thumbnail_url']
                existing_clip.duration = clip['duration']
                existing_clip.is_featured = clip['is_featured']
            else:
                # Create a new clip if it doesn't exist
                new_clip = Clip(
                    twitch_id=clip['id'],
                    url=clip['url'],
                    embed_url=clip['embed_url'],
                    broadcaster_id=clip['broadcaster_id'],
                    broadcaster_name=clip['broadcaster_name'],
                    creator_id=clip['creator_id'],
                    creator_name=clip['creator_name'],
                    video_id=clip['video_id'],
                    game_id=clip['game_id'],
                    language=clip['language'],
                    title=clip['title'],
                    view_count=clip['view_count'],
                    created_at=clip['created_at'],
                    thumbnail_url=clip['thumbnail_url'],
                    duration=clip['duration'],
                    vod_offset=clip['vod_offset'],
                    is_featured=clip['is_featured']
                )
                clips_to_add.append(new_clip)

        if clips_to_add:
            db.session.add_all(clips_to_add)
        db.session.commit()
        return redirect(url_for('main.index'))
    else:
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

# scheduler.add_job(check_access_token, 'interval', hours=1)

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
        user = User(twitch_id=user_id, 
                    login=user_login, 
                    display_name=user_display_name, 
                    profile_image_url=user_profile_image_url,
                    access_token=oauth2_token,
                    refresh_token=user_refresh_token,
                    rank_id=1)
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
    scheduler.start()
    return redirect(url_for('main.index'))