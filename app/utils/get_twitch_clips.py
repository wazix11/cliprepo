from datetime import datetime
from urllib.parse import urlencode
from dotenv import load_dotenv
import os, requests


load_dotenv(override=True)

TWITCH_CLIENT_ID = os.environ.get('TWITCH_CLIENT_ID')
TWITCH_CLIENT_SECRET = os.environ.get('TWITCH_CLIENT_SECRET')
TWITCH_CLIENT_ACCESS_TOKEN = ''
TWITCH_TOKEN_URL = 'https://id.twitch.tv/oauth2/token'
TWITCH_CLIP_URL = 'https://api.twitch.tv/helix/clips'


def get_twitch_access_token():
    global TWITCH_CLIENT_ACCESS_TOKEN
    params = {
        'client_id': TWITCH_CLIENT_ID,
        'client_secret': TWITCH_CLIENT_SECRET,
        'grant_type': 'client_credentials'
    }
    response = requests.post(TWITCH_TOKEN_URL, data=params)
    if response.status_code == 200:
        data = response.json()
        TWITCH_CLIENT_ACCESS_TOKEN = data['access_token']
    return TWITCH_CLIENT_ACCESS_TOKEN

def fetch_clips_from_twitch(params):
    if not TWITCH_CLIENT_ACCESS_TOKEN:
        get_twitch_access_token()
    
    headers = {
        'Authorization': f'Bearer {TWITCH_CLIENT_ACCESS_TOKEN}',
        'Client-Id': TWITCH_CLIENT_ID
    }
    
    qs = urlencode(params, doseq=True)
    response = requests.get(TWITCH_CLIP_URL + '?' + qs, headers=headers)
    
    if response.status_code == 401:
        # Token expired, refresh and retry
        get_twitch_access_token()
        return fetch_clips_from_twitch(params)
    
    if response.status_code == 200:
        return response.json()
    else:
        return {'data': [], 'error': response.json().get('message', 'Unknown error')}
    
def get_clips_by_broadcaster_id(broadcaster_id, started_at, ended_at=None, first=100, after=None):
    params = {
        'broadcaster_id': broadcaster_id,
        'first': first,
        'started_at': started_at.isoformat() if isinstance(started_at, datetime) else started_at
    }
    if ended_at:
        params['ended_at'] = ended_at.isoformat() if isinstance(ended_at, datetime) else ended_at
    if after:
        params['after'] = after
    
    return fetch_clips_from_twitch(params)

def get_clips_by_game_id(game_id, started_at, ended_at=None, first=100, after=None):
    params = {
        'game_id': game_id,
        'first': first,
        'started_at': started_at.isoformat() if isinstance(started_at, datetime) else started_at
    }
    if ended_at:
        params['ended_at'] = ended_at.isoformat() if isinstance(ended_at, datetime) else ended_at
    if after:
        params['after'] = after
    
    return fetch_clips_from_twitch(params)

def get_clips_by_id(clip_ids):
    if len(clip_ids) > 100:
        clip_ids = clip_ids[:100]

    params = {
        'id': clip_ids
    }

    return fetch_clips_from_twitch(params)