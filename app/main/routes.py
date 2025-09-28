from flask import render_template, render_template_string, send_from_directory, request, session
from flask_login import current_user
from datetime import datetime as dt, timedelta, timezone
from app.main.forms import *
from app.main import bp
from dotenv import load_dotenv
from app.models import *
from sqlalchemy import func

load_dotenv()

def format_count(count, type):
    if count < 1000:
        return str(count) + f' {type}{'s' if count != 1 else ''}'
    elif count < 1_000_000:
        return f'{count / 1000:.1f}K {type}s'
    elif count < 1_000_000_000:
        return f'{count / 1_000_000:.1f}M {type}s'

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
    
def format_clips(page, sort, timeframe, category=None, themes=[], subjects=[], layout=None, search=''):
    now = dt.now(timezone.utc)
    per_page = 12
    filters = []
    if category:
        filters.append(Clip.category_id == category)
    if themes:
        for theme_id in themes:
            filters.append(Clip.themes.any(Theme.id == theme_id))
    if subjects:
        for subject_id in subjects:
            filters.append(Clip.subjects.any(Subject.id == subject_id))
    if layout:
        filters.append(Clip.layout_id == layout)
    if search:
        search_pattern = f"%{search.strip()}%"
        filters.append(Clip.title.ilike(search_pattern) | 
                       Clip.title_override.ilike(search_pattern) |
                       Clip.broadcaster_name.ilike(search_pattern) | 
                       Clip.creator_name.ilike(search_pattern) |
                       Clip.category.has(Category.name.ilike(search_pattern)) |
                       Clip.themes.any(Theme.name.ilike(search_pattern)) |
                       Clip.subjects.any(Subject.name.ilike(search_pattern)) |
                       Clip.layout.has(Layout.name.ilike(search_pattern)))
    
    if sort == 'new':
        order_by = Clip.created_at.desc()
    elif sort == 'old':
        order_by = Clip.created_at.asc()
    elif sort == 'likes':
        order_by = func.count(upvotes.c.user_id).desc()
    else:
        order_by = Clip.view_count.desc()
    
    if timeframe == '24h':
        last_24_hours = now - timedelta(days=1)
        filters.append(Clip.created_at >= last_24_hours)
    elif timeframe == '7d':
        last_7_days = now - timedelta(days=7)
        filters.append(Clip.created_at >= last_7_days)
    elif timeframe == '30d':
        last_30_days = now - timedelta(days=30)
        filters.append(Clip.created_at >= last_30_days)
    elif timeframe == '1y':
        last_1_year = now - timedelta(days=365)
        filters.append(Clip.created_at >= last_1_year)

    filters.append(Clip.status.has(Status.type != 'Hidden'))
    filters.append(Clip.status.has(Status.type != 'Pending'))

    if sort == 'likes':
        query = Clip.query.outerjoin(upvotes).group_by(Clip.id).filter(*filters)
    else:
        query = Clip.query.filter(*filters)
    clips = query.order_by(order_by).paginate(page=page, per_page=per_page, error_out=False)

    formatted_clips = [{
        'twitch_id': clip.twitch_id,
        'url': clip.url,
        'embed_url': clip.embed_url,
        'broadcaster_name': clip.broadcaster_name,
        'creator_name': clip.creator_name,
        'title': clip.title,
        'title_override': clip.title_override,
        'view_count': format_count(clip.view_count, 'view'),
        'created_at': clip.created_at,
        'created_at_formatted': format_upload_date(clip.created_at),
        'thumbnail_url': clip.thumbnail_url,
        'duration': clip.duration,
        'category': clip.category,
        'themes': clip.themes,
        'subjects': clip.subjects,
        'layout': clip.layout,
        'status': clip.status,
        'upvotes': format_count(len(clip.upvoted_by), 'like'),
        'liked': current_user.is_authenticated and current_user in clip.upvoted_by
    } for clip in clips.items]
    has_next = clips.has_next
    
    return formatted_clips, has_next

def set_session_filters(route, sort='views', timeframe='all', category='', themes=[], subjects=[], layout='', search=''):
    session[route] = {
        'sort': sort,
        'timeframe': timeframe,
        'category': category,
        'themes': themes,
        'subjects': subjects,
        'layout': layout,
        'search': search
    }

def get_session_filters(route):
    if route in session:
        return session[route]
    return {
        'sort': 'views',
        'timeframe': 'all',
        'category': None,
        'themes': [],
        'subjects': [],
        'layout': None,
        'search': ''
    }
    
def get_value(request_value, session_value, default):
    if request_value is not None:
        return request_value
    if session_value is not None:
        return session_value
    return default

@bp.route('/like-clip/<twitch_id>', methods=['POST'])
def like_clip(twitch_id):
    clip = Clip.query.filter_by(twitch_id=twitch_id).first_or_404()
    liked = False
    
    if current_user.is_authenticated and clip:
        if current_user in clip.upvoted_by:
            clip.upvoted_by.remove(current_user)
        else:
            clip.upvoted_by.append(current_user)
        db.session.commit()
        liked = current_user in clip.upvoted_by
    
    return render_template_string("""
        <span id="like-btn-{{ clip.twitch_id }}">
            <button class="btn clip-like-btn {% if liked %}btn-danger{% else %}btn-success{% endif %}" 
                    type="button"
                    hx-post="/like-clip/{{ clip.twitch_id }}"
                    hx-target="#like-btn-{{ clip.twitch_id }}"
                    hx-swap="outerHTML">
                {% if liked %}
                    <i class="fa-solid fa-heart"></i>
                {% else %}
                    <i class="fa-regular fa-heart"></i>
                {% endif %}
            </button>
            <span class="clip-like-count" id="like-count-{{ clip.twitch_id }}">{{ upvotes }}</span>
        </span>
    """, clip=clip, liked=liked, upvotes=format_count(len(clip.upvoted_by), 'like'))

@bp.route('/favicon.ico')
def favicon():
    return send_from_directory('static', 'favicon.ico')

# Home page
@bp.route('/', methods=['GET', 'POST'])
def index():
    categories = Category.query.order_by('id').all()
    theme_choices = Theme.query.order_by('id').all()
    subject_choices = Subject.query.order_by('id').all()
    layout_choices = Layout.query.order_by('id').all()
    subject_categories = []

    # Group subjects by category
    for sc in SubjectCategory.query.order_by('id'):
        sc_subject_choices = Subject.query.filter(Subject.category_id == sc.id).order_by('id').all()
        if not sc_subject_choices:
            continue
        group_choices = []
        for su in sc_subject_choices:
            group_choices.append({
                'id': su.id, 
                'name': su.name,
                'subtext': su.subtext or '',
                'keywords': su.keywords or ''
                })
        subject_categories.append((sc.name, group_choices))
    
    # Get filters from session
    session_filters = get_session_filters('main')
    sort = get_value(None, session_filters.get('sort'), default='views')
    timeframe = get_value(None, session_filters.get('timeframe'), 'all')
    category = get_value(None, session_filters.get('category'), None)
    themes = get_value(None, session_filters.get('themes', []), [])
    subjects = get_value(None, session_filters.get('subjects', []), [])
    layout = get_value(None, session_filters.get('layout'), None)
    search = get_value(None, session_filters.get('search'), '')
    page = 1
    
    formatted_clips, has_next = format_clips(page, sort, timeframe, category, themes, subjects, layout, search)
    return render_template(
        'index.html',
        title='Home',
        categories=categories,
        themes=theme_choices,
        subjects=subject_choices,
        layouts=layout_choices,
        subject_categories=subject_categories,
        clips=formatted_clips,
        has_next=has_next,
        currentPage=2,
        sort=sort,
        timeframe=timeframe,
        selected_category=category,
        selected_themes=themes,
        selected_subjects=subjects,
        selected_layout=layout,
        search=search
    )

# Loads more clips and adds them to the main page as you scroll down
@bp.route('/load-clips', methods=['POST'])
def load_clips():
    session_filters = get_session_filters('main')
    page = request.args.get('page', 1, type=int)
    sort = get_value(request.form.get('sort'), session_filters.get('sort'), 'views')
    timeframe = get_value(request.form.get('timeframe'), session_filters.get('timeframe'), 'all')
    category = get_value(request.form.get('category'), session_filters.get('category'), None)
    if category in [None, '', 'null']:
        category = None
    
    layout = get_value(request.form.get('layout'), session_filters.get('layout'), None)
    if layout in [None, '', 'null']:
        layout = None

    themes_raw = get_value(request.form.getlist('themes'), session_filters.get('themes'), [])
    if isinstance(themes_raw, str):
        themes = [t for t in themes_raw.split(',') if t]
    elif isinstance(themes_raw, list):
        themes = [t for t in themes_raw if t]
    else:
        themes = []

    subjects_raw = get_value(request.form.getlist('subjects'), session_filters.get('subjects'), [])
    if isinstance(subjects_raw, str):
        subjects = [s for s in subjects_raw.split(',') if s]
    elif isinstance(subjects_raw, list):
        subjects = [s for s in subjects_raw if s]
    else:
        subjects = []

    search = get_value(request.form.get('search'), session_filters.get('search'), '')
    
    # Set session filters
    set_session_filters('main', sort, timeframe, category, themes, subjects, layout, search)

    # Sort and paginate
    formatted_clips, has_next = format_clips(page, sort, timeframe, category, themes, subjects, layout, search)
    return render_template(
        'additional_clips.html', 
        currentPage=page+1, 
        sort=sort, 
        timeframe=timeframe, 
        clips=formatted_clips, 
        has_next=has_next
    )

@bp.route('/about')
def about():
    return render_template('main/about.html', title='About')

@bp.route('/leaderboard')
def leaderboard():
    return render_template('main/leaderboard.html', title='Leaderboard')

@bp.route('/clips')
def clips():
    pass