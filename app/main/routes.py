from flask import render_template, flash, redirect, url_for, current_app, request, session
import re, time, os
from datetime import datetime as dt, timedelta, timezone
from flask_login import current_user, login_required
from app.main.forms import *
from app.main import bp
from dotenv import load_dotenv
from app.models import *

load_dotenv()

def format_view_count(view_count):
    if view_count < 1000:
        return str(view_count) + ' views'
    elif view_count < 1_000_000:
        return f'{view_count / 1000:.1f}K views'
    elif view_count < 1_000_000_000:
        return f'{view_count / 1_000_000:.1f}M views'

def format_upload_date(upload_date_str):
    upload_date = dt.fromisoformat(upload_date_str.replace('Z', '+00:00'))
    now = dt.now(timezone.utc)
    diff = now - upload_date
    seconds = diff.total_seconds()
    minutes = seconds // 60
    hours = minutes // 60
    days = hours // 24
    months = days // 30
    years = months // 12

    if years > 0:
        return f"{int(years)} year{'s' if years > 1 else ''} ago"
    elif months > 0:
        return f"{int(months)} month{'s' if months > 1 else ''} ago"
    elif days > 0:
        return f"{int(days)} day{'s' if days > 1 else ''} ago"
    elif hours > 0:
        return f"{int(hours)} hour{'s' if hours > 1 else ''} ago"
    elif minutes > 0:
        return f"{int(minutes)} minute{'s' if minutes > 1 else ''} ago"
    else:
        return f"{int(seconds)} second{'s' if seconds > 1 else ''} ago"
    
def format_clips(page, sort, timeframe):
    now = dt.now(timezone.utc)
    per_page = 12
    if sort == 'new':
        clips_new = Clip.query.filter(Clip.duration != 0)
        clips = clips_new.order_by(Clip.created_at.desc()).paginate(page=page, per_page=per_page, error_out=False)
    elif sort == 'old':
        clips_old = Clip.query.filter(Clip.duration != 0)
        clips = clips_old.order_by(Clip.created_at.asc()).paginate(page=page, per_page=per_page, error_out=False)
    else:
        if timeframe == '24h':
            last_24_hours = now - timedelta(days=1)
            clips_last_24_hours = Clip.query.filter(Clip.created_at >= last_24_hours)
            clips = clips_last_24_hours.order_by(Clip.view_count.desc()).paginate(page=page, per_page=per_page, error_out=False)
        elif timeframe == '7d':
            last_7_days = now - timedelta(days=7)
            clips_last_7_days = Clip.query.filter(Clip.created_at >= last_7_days)
            clips = clips_last_7_days.order_by(Clip.view_count.desc()).paginate(page=page, per_page=per_page, error_out=False)
        elif timeframe == '30d':
            last_30_days = now - timedelta(days=30)
            clips_last_30_days = Clip.query.filter(Clip.created_at >= last_30_days)
            clips = clips_last_30_days.order_by(Clip.view_count.desc()).paginate(page=page, per_page=per_page, error_out=False)
        elif timeframe == '1y':
            last_1_year = now - timedelta(days=365)
            clips_last_1_year = Clip.query.filter(Clip.created_at >= last_1_year)
            clips = clips_last_1_year.order_by(Clip.view_count.desc()).paginate(page=page, per_page=per_page, error_out=False)
        else:
            clips_all_time = Clip.query.filter(Clip.duration != 0)
            clips = clips_all_time.order_by(Clip.view_count.desc()).paginate(page=page, per_page=per_page, error_out=False)
    formatted_clips = [{
        'url': clip.url,
        'embed_url': clip.embed_url,
        'broadcaster_name': clip.broadcaster_name,
        'creator_name': clip.creator_name,
        'title': clip.title,
        'view_count': format_view_count(clip.view_count),
        'created_at': format_upload_date(clip.created_at),
        'thumbnail_url': clip.thumbnail_url,
        'duration': clip.duration,
        'category': clip.category,
        'themes': clip.themes,
        'subjects': clip.subjects,
        'status': clip.status
    } for clip in clips.items]
    has_next = clips.has_next
    
    return formatted_clips, has_next

# Home page
@bp.route('/')
def index():
    form = ClipFilterForm()
    sort = request.args.get('sort', 'top', type=str)
    timeframe = request.args.get('timeframe', 'all', type=str)
    return render_template('index.html', title='Home', sort=sort, timeframe=timeframe)

# Loads more clips and adds them to the main page as you scroll down
@bp.route('/load-clips')
def load_clips():
    page = request.args.get('page', 2, type=int)
    sort = request.args.get('sort', 'top', type=str)
    timeframe = request.args.get('timeframe', 'all', type=str)
    formatted_clips, has_next = format_clips(page, sort, timeframe)
    return render_template('additional_clips.html', currentPage=page+1, sort=sort, timeframe=timeframe, clips=formatted_clips, has_next=has_next)

@bp.route('/about')
def about():
    return render_template('main/about.html', title='About')

@bp.route('/leaderboard')
def leaderboard():
    return render_template('main/leaderboard.html', title='Leaderboard')

@bp.route('/clips')
def clips():
    pass