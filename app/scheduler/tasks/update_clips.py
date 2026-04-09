import os
from dotenv import load_dotenv
from app import db
from app.models import Clip, User
from app.utils.get_twitch_clips import get_clips_by_broadcaster_id, get_clips_by_game_id, get_clips_by_id
from datetime import datetime, timedelta, timezone

load_dotenv(override=True)
BROADCASTER_ID = os.environ.get('BROADCASTER_ID')
GAME_ID = os.environ.get('GAME_ID')
CLIPS_START_DATE = os.environ.get("CLIPS_START_DATE")

def update_clips(started_at=None, after=None, save_to_file=True):
    latest_clip_file = './app/scheduler/latest_clip_created_at.txt'
    if started_at is None:
        started_at = CLIPS_START_DATE
        if os.path.exists(latest_clip_file):
            with open(latest_clip_file, 'r') as f:
                started_at = f.read().strip()
    users_to_add = []
    clips_to_add = []
    while True:
        if BROADCASTER_ID != "" and BROADCASTER_ID is not None:
            clips_data = get_clips_by_broadcaster_id(BROADCASTER_ID, started_at, after=after)
            if 'error' in clips_data:
                break
        elif GAME_ID != "" and GAME_ID is not None:
            clips_data = get_clips_by_game_id(GAME_ID, started_at, after=after)
            if 'error' in clips_data:
                break
        latest_created_at = None
        for clip in clips_data['data']:
            # Track the latest created_at
            if latest_created_at is None or clip['created_at'] > latest_created_at:
                latest_created_at = clip['created_at']

            existing_user = User.query.filter_by(twitch_id=clip['creator_id']).first()
            if any(u.twitch_id == clip['creator_id'] for u in users_to_add):
                continue
            if existing_user:
                changed = False
                if existing_user.display_name != clip['creator_name'] and clip['creator_name']:
                    existing_user.display_name = clip['creator_name']; changed = True
                
                if changed:
                    existing_user.updated_at = datetime.now(timezone.utc)
            else:
                new_user = User(
                    twitch_id=clip['creator_id'],
                    display_name=clip['creator_name'] if clip['creator_name'] else f'User {clip['creator_id']}'
                )
                users_to_add.append(new_user)

            existing_clip = Clip.query.filter_by(twitch_id=clip['id']).first()
            new_clip = None
            if any(c.twitch_id == clip['id'] for c in clips_to_add):
                continue
            if existing_clip:
                changed = False
                # Update existing clip fields
                if existing_clip.url != clip['url']:
                    existing_clip.url = clip['url']; changed = True
                if existing_clip.embed_url != clip['embed_url']:
                    existing_clip.embed_url = clip['embed_url']; changed = True
                if existing_clip.broadcaster_id != int(clip['broadcaster_id']):
                    existing_clip.broadcaster_id = int(clip['broadcaster_id']); changed = True
                if existing_clip.broadcaster_name != clip['broadcaster_name']:
                    existing_clip.broadcaster_name = clip['broadcaster_name']; changed = True
                if existing_clip.creator_id != int(clip['creator_id']):
                    existing_clip.creator_id = int(clip['creator_id']); changed = True
                if existing_clip.creator_name != clip['creator_name']:
                    existing_clip.creator_name = clip['creator_name']; changed = True
                if existing_clip.title != clip['title']:
                    existing_clip.title = clip['title']; changed = True
                if existing_clip.view_count != clip['view_count']:
                    existing_clip.view_count = clip['view_count']; changed = True
                if existing_clip.created_at != clip['created_at']:
                    existing_clip.created_at = clip['created_at']; changed = True
                if existing_clip.vod_offset != clip['vod_offset']:
                    existing_clip.vod_offset = clip['vod_offset']; changed = True
                if existing_clip.thumbnail_url != clip['thumbnail_url']:
                    existing_clip.thumbnail_url = clip['thumbnail_url']; changed = True
                if existing_clip.duration != clip['duration']:
                    existing_clip.duration = clip['duration']; changed = True
                if existing_clip.is_featured != clip.get('is_featured', False):
                    existing_clip.is_featured = clip.get('is_featured', False); changed = True

                if changed:
                    existing_clip.updated_at = datetime.now(timezone.utc)
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
                    updated_at=datetime.now(timezone.utc),
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
    if users_to_add:
        db.session.add_all(users_to_add)
    db.session.commit()

def update_manual_import_clips(offset):
    # no need to manually import clips if going based on GAME_ID
    if GAME_ID and not BROADCASTER_ID:
        return
    
    manual_clips = db.session.query(Clip.twitch_id)\
        .filter(Clip.broadcaster_id != BROADCASTER_ID)\
        .order_by(Clip.created_at.desc())\
        .offset(offset)\
        .limit(100)\
        .all()
    manual_clip_ids = [c.twitch_id for c in manual_clips]

    clip_offset_file = './app/scheduler/manual_import_clip_offset.txt'
    if len(manual_clip_ids) == 0:
        # if no clips returned, end of list has been reached, reset offset to 0 to start over
        with open(clip_offset_file, 'w') as f:
            f.write('0')
    elif len(manual_clip_ids) <= 100:
        with open(clip_offset_file, 'w') as f:
            f.write(str(offset + len(manual_clip_ids)))
    else:
        with open(clip_offset_file, 'w') as f:
            f.write(str(offset + 100))

    clips_data = get_clips_by_id(manual_clip_ids)
    if 'error' in clips_data:
        return

    users_to_add = []
    for clip in clips_data['data']:
        existing_user = User.query.filter_by(twitch_id=clip['creator_id']).first()
        if any(u.twitch_id == clip['creator_id'] for u in users_to_add):
            continue
        if existing_user:
            changed = False
            if existing_user.display_name != clip['creator_name'] and clip['creator_name']:
                existing_user.display_name = clip['creator_name']; changed = True
            
            if changed:
                existing_user.updated_at = datetime.now(timezone.utc)
        else:
            new_user = User(
                twitch_id=clip['creator_id'],
                display_name=clip['creator_name'] if clip['creator_name'] else f'User {clip['creator_id']}'
            )
            users_to_add.append(new_user)

        existing_clip = Clip.query.filter_by(twitch_id=clip['id']).first()
        changed = False
        # Update existing clip fields
        if existing_clip.url != clip['url']:
            existing_clip.url = clip['url']; changed = True
        if existing_clip.embed_url != clip['embed_url']:
            existing_clip.embed_url = clip['embed_url']; changed = True
        if existing_clip.broadcaster_id != int(clip['broadcaster_id']):
            existing_clip.broadcaster_id = int(clip['broadcaster_id']); changed = True
        if existing_clip.broadcaster_name != clip['broadcaster_name']:
            existing_clip.broadcaster_name = clip['broadcaster_name']; changed = True
        if existing_clip.creator_id != int(clip['creator_id']):
            existing_clip.creator_id = int(clip['creator_id']); changed = True
        if existing_clip.creator_name != clip['creator_name']:
            existing_clip.creator_name = clip['creator_name']; changed = True
        if existing_clip.title != clip['title']:
            existing_clip.title = clip['title']; changed = True
        if existing_clip.view_count != clip['view_count']:
            existing_clip.view_count = clip['view_count']; changed = True
        if existing_clip.created_at != clip['created_at']:
            existing_clip.created_at = clip['created_at']; changed = True
        if existing_clip.vod_offset != clip['vod_offset']:
            existing_clip.vod_offset = clip['vod_offset']; changed = True
        if existing_clip.thumbnail_url != clip['thumbnail_url']:
            existing_clip.thumbnail_url = clip['thumbnail_url']; changed = True
        if existing_clip.duration != clip['duration']:
            existing_clip.duration = clip['duration']; changed = True
        if existing_clip.is_featured != clip.get('is_featured', False):
            existing_clip.is_featured = clip.get('is_featured', False); changed = True

        if changed:
            existing_clip.updated_at = datetime.now(timezone.utc)

    if users_to_add:
        db.session.add_all(users_to_add)
    db.session.commit()