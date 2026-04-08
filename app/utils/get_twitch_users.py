from urllib.parse import urlencode
from dotenv import load_dotenv
import os, requests


load_dotenv(override=True)

TWITCH_CLIENT_ID = os.environ.get('TWITCH_CLIENT_ID')
TWITCH_CLIENT_SECRET = os.environ.get('TWITCH_CLIENT_SECRET')
TWITCH_CLIENT_ACCESS_TOKEN = ''
TWITCH_TOKEN_URL = 'https://id.twitch.tv/oauth2/token'
TWITCH_USERS_URL = 'https://api.twitch.tv/helix/users'

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

def fetch_users_from_twitch(params):
    if not TWITCH_CLIENT_ACCESS_TOKEN:
        get_twitch_access_token()

    headers = {
        'Authorization': f'Bearer {TWITCH_CLIENT_ACCESS_TOKEN}',
        'Client-Id': TWITCH_CLIENT_ID
    }

    qs = urlencode(params, doseq=True)
    response = requests.get(TWITCH_USERS_URL + '?' + qs, headers=headers)
    
    if response.status_code == 401:
        # Token expired, refresh and retry
        get_twitch_access_token()
        return fetch_users_from_twitch(params)
    
    if response.status_code == 200:
        return response.json()
    else:
        return {'data': [], 'error': response.json().get('message', 'Unknown error')}

def get_user_by_login(login):
    params = {
        'login': login
    }
    return fetch_users_from_twitch(params)