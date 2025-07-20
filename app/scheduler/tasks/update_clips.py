import os, requests
from urllib.parse import urlencode
from dotenv import load_dotenv
from app import db
from app.models import Clip
from datetime import datetime, timedelta, timezone

load_dotenv()
TWITCH_CLIENT_ID = os.environ.get('TWITCH_CLIENT_ID')
TWITCH_CLIENT_SECRET = os.environ.get('TWITCH_CLIENT_SECRET')
TWITCH_CLIENT_ACCESS_TOKEN = ''
TWITCH_TOKEN_URL = 'https://id.twitch.tv/oauth2/token'
TWITCH_CLIP_URL = 'https://api.twitch.tv/helix/clips'
BROADCASTER_ID = os.environ.get('BROADCASTER_ID')

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

def get_clips(started_at, after=None):
    if TWITCH_CLIENT_ACCESS_TOKEN == '':
        update_client_credentials()

    headers = {
        'Authorization': f'Bearer {TWITCH_CLIENT_ACCESS_TOKEN}',
        'Client-Id': TWITCH_CLIENT_ID
    }
    qs = urlencode({
        'broadcaster_id': BROADCASTER_ID,
        'first': 100,
        'started_at': started_at,
    })
    if after:
        qs += f'&after={after}'
    response = requests.get(TWITCH_CLIP_URL + '?' + qs, headers=headers)
    if response.status_code == 401:
        print("Access token expired, updating credentials...")
        update_client_credentials()
        return get_clips(started_at, after)
    data = response.json()
    return data

def update_clips(started_at=None, after=None, save_to_file=True):
    latest_clip_file = './app/scheduler/latest_clip_created_at.txt'
    if started_at is None:
        started_at = '2021-07-21T00:00:00Z'
        if os.path.exists(latest_clip_file):
            with open(latest_clip_file, 'r') as f:
                started_at = f.read().strip()
    clips_to_add = []
    while True:
        clips_data = get_clips(started_at, after)
        latest_created_at = None
        for clip in clips_data['data']:
            # Track the latest created_at
            if latest_created_at is None or clip['created_at'] > latest_created_at:
                latest_created_at = clip['created_at']

            existing_clip = Clip.query.filter_by(twitch_id=clip['id']).first()
            new_clip = None
            if any(c.twitch_id == clip['id'] for c in clips_to_add):
                continue
            if existing_clip:
                # Update existing clip fields
                existing_clip.url = clip['url']
                existing_clip.embed_url = clip['embed_url']
                existing_clip.broadcaster_id = int(clip['broadcaster_id'])
                existing_clip.broadcaster_name = clip['broadcaster_name']
                existing_clip.creator_id = int(clip['creator_id'])
                existing_clip.creator_name = clip['creator_name']
                existing_clip.title = clip['title']
                existing_clip.view_count = clip['view_count']
                existing_clip.created_at = clip['created_at']
                existing_clip.thumbnail_url = clip['thumbnail_url']
                existing_clip.duration = clip['duration']
                existing_clip.is_featured = clip.get('is_featured', False)
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
                    is_featured=clip.get('is_featured', False),
                    status_id=1
                )
            if new_clip:
                clips_to_add.append(new_clip)

        previous_created_at = None
        if os.path.exists(latest_clip_file):
            with open(latest_clip_file, 'r') as f:
                previous_created_at = f.read().strip()
        if not previous_created_at:
            previous_created_at = started_at

        # Save the most recent created_at to a text file if it's new or updated
        if latest_created_at:
            if latest_created_at != previous_created_at and latest_created_at > previous_created_at:
                print(f"Latest clip created at: {latest_created_at}")
                if save_to_file:
                    with open(latest_clip_file, 'w') as f:
                        f.write(latest_created_at)
            elif latest_created_at == previous_created_at:
                # Only add 6 days if latest_created_at is the same as previous
                dt = datetime.fromisoformat(latest_created_at.replace('Z', '+00:00'))
                dt_plus_6_days = dt + timedelta(days=6)
                new_created_at = dt_plus_6_days.isoformat(timespec='seconds').replace('+00:00', 'Z')
                # Check if new_created_at is after current datetime
                now = datetime.now(timezone.utc).isoformat(timespec='seconds').replace('+00:00', 'Z')
                if new_created_at > now:
                    new_created_at = now
                print(f"No new clips found. Advancing created_at to: {new_created_at}")
                if save_to_file:
                    with open(latest_clip_file, 'w') as f:
                        f.write(new_created_at)
                latest_created_at = new_created_at
        elif previous_created_at:
            # If no latest_created_at found, use previous and add 6 days
            dt = datetime.fromisoformat(previous_created_at.replace('Z', '+00:00'))
            dt_plus_6_days = dt + timedelta(days=6)
            new_created_at = dt_plus_6_days.isoformat(timespec='seconds').replace('+00:00', 'Z')
            # Check if new_created_at is after current datetime
            now = datetime.now(timezone.utc).isoformat(timespec='seconds').replace('+00:00', 'Z')
            if new_created_at > now:
                new_created_at = now
            print(f"No clips found. Advancing created_at to: {new_created_at}")
            if save_to_file:
                with open(latest_clip_file, 'w') as f:
                    f.write(new_created_at)
            latest_created_at = new_created_at


        # Check for pagination cursor
        after = clips_data.get('pagination', {}).get('cursor')
        if not after:
            break

    if clips_to_add:
        db.session.add_all(clips_to_add)
    db.session.commit()