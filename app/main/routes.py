from flask import render_template, render_template_string, send_from_directory, request, session, make_response, current_app
from flask_login import current_user
from datetime import datetime as dt, timedelta, timezone
from app.main.forms import *
from app.main import bp
from dotenv import load_dotenv
from app.models import *
from sqlalchemy import func, or_
import os, json, random

load_dotenv(override=True)
EMBED_PARENT = os.environ.get('EMBED_PARENT')

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
    
def format_clips(page, sort, timeframe='7d', category=None, broadcasters=[], themes=[], subjects=[], layout=None, search='', liked=False):
    now = dt.now(timezone.utc)
    per_page = 12
    filters = []
    if category:
        filters.append(Clip.category_id == category)
    if broadcasters:
        filters.append(or_(*[Clip.broadcaster_id == bid for bid in broadcasters]))
    if themes:
        for theme_id in themes:
            filters.append(Clip.themes.any(Theme.id == theme_id))
    if subjects:
        for subject_id in subjects:
            filters.append(Clip.subjects.any(Subject.id == subject_id))
    if layout:
        filters.append(Clip.layout_id == layout)
    if liked and current_user.is_authenticated:
        filters.append(Clip.upvoted_by.any(User.id == current_user.id))
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

@bp.route('/like-clip/<twitch_id>', methods=['POST'])
def like_clip(twitch_id):
    clip = Clip.query.filter_by(twitch_id=twitch_id).first_or_404()
    liked = False
    
    if not current_user.is_authenticated:
        response = make_response(render_template_string("""
            <span id="like-btn-{{ clip.twitch_id }}">
                <button class="btn clip-like-btn btn-success" 
                        type="button"
                        hx-post="/like-clip/{{ clip.twitch_id }}"
                        hx-target="#like-btn-{{ clip.twitch_id }}"
                        hx-swap="outerHTML">
                    <i class="fa-regular fa-heart"></i>
                </button>
                <span class="clip-like-count" id="like-count-{{ clip.twitch_id }}">{{ upvotes }}</span>
            </span>
        """, clip=clip, upvotes=format_count(len(clip.upvoted_by), 'like')))
        response.headers['HX-Trigger'] = json.dumps({"showLoginMessage": "Please log in to like clips"})
        return response
    
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

VALID_SORTS = {'views', 'new', 'old', 'likes'}
VALID_TIMEFRAMES = {'24h', '7d', '30d', '1y', 'all'}

# Home page
@bp.route('/', methods=['GET', 'POST'])
def index():
    broadcaster_choices = db.session.query(Clip.broadcaster_id, Clip.broadcaster_name).distinct().all()
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
    
    page = 1
    sort = request.args.get('sort', 'views')
    if sort not in VALID_SORTS:
        sort = 'views'
    timeframe = request.args.get('timeframe', '7d')
    if timeframe not in VALID_TIMEFRAMES:
        timeframe = '7d'
    category = request.args.get('category', None)
    if category:
        if not category.isdigit() or not Category.query.get(int(category)):
            category = None
    if category in [None, '', 'null']: category = None
    layout = request.args.get('layout', None)
    if layout:
        if not layout.isdigit() or not Layout.query.get(int(layout)):
            layout = None
    if layout in [None, '', 'null']: layout = None
    search = request.args.get('search', '')
    if len(search) > 50:
        search = search[:50]
    liked = request.args.get('liked', '0') == '1'    

    broadcasters_raw = request.args.getlist('broadcasters') or []
    if isinstance(broadcasters_raw, str):
        broadcasters = [b for b in broadcasters_raw.split(',') if b]
    elif isinstance(broadcasters_raw, list):
        # Handle case where list contains a single comma-separated string
        if len(broadcasters_raw) == 1 and ',' in broadcasters_raw[0]:
            broadcasters = [b for b in broadcasters_raw[0].split(',') if b]
        else:
            broadcasters = [b for b in broadcasters_raw if b]
    else:
        broadcasters = []

    themes_raw = request.args.getlist('themes') or []
    if isinstance(themes_raw, str):
        themes = [t for t in themes_raw.split(',') if t]
    elif isinstance(themes_raw, list):
        if len(themes_raw) == 1 and ',' in themes_raw[0]:
            themes = [t for t in themes_raw[0].split(',') if t]
        else:
            themes = [t for t in themes_raw if t]
    else:
        themes = []

    subjects_raw = request.args.getlist('subjects') or []
    if isinstance(subjects_raw, str):
        subjects = [s for s in subjects_raw.split(',') if s]
    elif isinstance(subjects_raw, list):
        if len(subjects_raw) == 1 and ',' in subjects_raw[0]:
            subjects = [s for s in subjects_raw[0].split(',') if s]
        else:
            subjects = [s for s in subjects_raw if s]
    else:
        subjects = []

    formatted_clips, has_next = format_clips(
        page=page,
        sort=sort,
        timeframe=timeframe,
        category=category,
        broadcasters=broadcasters,
        themes=themes,
        subjects=subjects,
        layout=layout,
        search=search,
        liked=liked
    )
    return render_template(
        'index.html',
        title='Home',
        broadcaster_choices=broadcaster_choices,
        categories=categories,
        theme_choices=theme_choices,
        subject_choices=subject_choices,
        layout_choices=layout_choices,
        subject_categories=subject_categories,
        clips=formatted_clips,
        has_next=has_next,
        currentPage=2,
        sort=sort,
        timeframe=timeframe,
        selected_category=category,
        selected_broadcasters=broadcasters,
        selected_themes=themes,
        selected_subjects=subjects,
        selected_layout=layout,
        search=search,
        liked=liked
    )

# Loads more clips and adds them to the main page as you scroll down
@bp.route('/load-clips', methods=['POST'])
def load_clips():
    page = request.args.get('page', 1, type=int)
    sort = request.values.get('sort', 'views')
    timeframe = request.values.get('timeframe', '7d')
    category = request.values.get('category', None)
    if category in [None, '', 'null']:
        category = None
    layout = request.values.get('layout', None)
    if layout in [None, '', 'null']:
        layout = None

    broadcasters_raw = request.values.getlist('broadcasters')
    if isinstance(broadcasters_raw, str):
        broadcasters = [b for b in broadcasters_raw.split(',') if b]
    elif isinstance(broadcasters_raw, list):
        # Handle case where list contains a single comma-separated string
        if len(broadcasters_raw) == 1 and ',' in broadcasters_raw[0]:
            broadcasters = [b for b in broadcasters_raw[0].split(',') if b]
        else:
            broadcasters = [b for b in broadcasters_raw if b]
    else:
        broadcasters = []

    themes_raw = request.values.getlist('themes')
    if isinstance(themes_raw, str):
        themes = [t for t in themes_raw.split(',') if t]
    elif isinstance(themes_raw, list):
        themes = [t for t in themes_raw if t]
    else:
        themes = []

    subjects_raw = request.values.getlist('subjects')
    if isinstance(subjects_raw, str):
        subjects = [s for s in subjects_raw.split(',') if s]
    elif isinstance(subjects_raw, list):
        subjects = [s for s in subjects_raw if s]
    else:
        subjects = []

    search = request.values.get('search', '')
    liked = request.values.get('liked', '0') == '1'

    # Sort and paginate
    formatted_clips, has_next = format_clips(
        page=page,
        sort=sort,
        timeframe=timeframe,
        category=category,
        broadcasters=broadcasters,
        themes=themes,
        subjects=subjects,
        layout=layout,
        search=search,
        liked=liked
    )
    return render_template(
        'additional_clips.html', 
        currentPage=page+1, 
        sort=sort, 
        timeframe=timeframe,
        category=category,
        broadcasters=broadcasters,
        themes=themes,
        subjects=subjects,
        layout=layout,
        search=search,
        liked=liked,
        clips=formatted_clips, 
        has_next=has_next
    )

@bp.route('/about')
def about():
    static_path = os.path.join(current_app.root_path, 'static')
    clip_png_files = [f for f in os.listdir(static_path) if f.lower().endswith('.png') and 'clip' in f.lower()] if os.path.exists(static_path) else []
    cliprepo_image = random.choice(clip_png_files) if clip_png_files else None
    domains = [
        {
            'cliprepo_url': 'https://cliprepo.com',
            'name': 'ClipRepo',
            'website_url': '',
            'stream_url': '',
            'image': cliprepo_image
        },
        {
            'cliprepo_url': 'https://alv.cliprepo.com',
            'name': 'Alveus Sanctuary',
            'website_url': 'https://www.alveussanctuary.org/',
            'stream_url': 'https://www.twitch.tv/alveussanctuary',
            'image': 'alveus_logo.png'
        },
        {
            'cliprepo_url': 'https://wbs.cliprepo.com',
            'name': 'World Bird Sanctuary',
            'website_url': 'https://www.worldbirdsanctuary.org/',
            'stream_url': 'https://www.twitch.tv/theworldbirdsanctuary',
            'image': 'wbs_logo.png'
        },
        {
            'cliprepo_url': 'https://wcc.cliprepo.com',
            'name': 'Wolf Conservation Center',
            'website_url': 'https://nywolf.org/',
            'stream_url': 'https://www.twitch.tv/wolfconservationcenter',
            'image': 'wcc_logo2.png'
        },
        {
            'cliprepo_url': 'https://wtw.cliprepo.com',
            'name': 'Window to Wildlife',
            'website_url': 'https://www.windowtowildlife.org/',
            'stream_url': 'https://www.twitch.tv/windowtowildlife',
            'image': 'wtw_logo.png'
        }
    ]
    return render_template('main/about.html', title='About', domains=domains)

@bp.route('/leaderboard')
def leaderboard():
    return render_template('main/leaderboard.html', title='Leaderboard')

@bp.route('/clip-queue', methods=['GET'])
def clip_queue():
    broadcaster_choices = db.session.query(Clip.broadcaster_id, Clip.broadcaster_name).distinct().all()
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

    page = 1
    sort = request.args.get('sort', 'views')
    if sort not in VALID_SORTS:
        sort = 'views'
    timeframe = request.args.get('timeframe', '7d')
    if timeframe not in VALID_TIMEFRAMES:
        timeframe = '7d'
    category = request.args.get('category', None)
    if category:
        if not category.isdigit() or not Category.query.get(int(category)):
             category = None
    if category in [None, '', 'null']: category = None
    layout = request.args.get('layout', None)
    if layout:
        if not layout.isdigit() or not Layout.query.get(int(layout)):
            layout = None
    if layout in [None, '', 'null']: layout = None
    search = request.args.get('search', '')
    if len(search) > 50:
        search = search[:50]
    liked = request.args.get('liked', '0') == '1'    

    broadcasters_raw = request.args.getlist('broadcasters') or []
    if isinstance(broadcasters_raw, str):
        broadcasters = [b for b in broadcasters_raw.split(',') if b]
    elif isinstance(broadcasters_raw, list):
        # Handle case where list contains a single comma-separated string
        if len(broadcasters_raw) == 1 and ',' in broadcasters_raw[0]:
            broadcasters = [b for b in broadcasters_raw[0].split(',') if b]
        else:
            broadcasters = [b for b in broadcasters_raw if b]
    else:
        broadcasters = []

    themes_raw = request.args.getlist('themes') or []
    if isinstance(themes_raw, str):
        themes = [t for t in themes_raw.split(',') if t]
    elif isinstance(themes_raw, list):
        if len(themes_raw) == 1 and ',' in themes_raw[0]:
            themes = [t for t in themes_raw[0].split(',') if t]
        else:
            themes = [t for t in themes_raw if t]
    else:
        themes = []

    subjects_raw = request.args.getlist('subjects') or []
    if isinstance(subjects_raw, str):
        subjects = [s for s in subjects_raw.split(',') if s]
    elif isinstance(subjects_raw, list):
        if len(subjects_raw) == 1 and ',' in subjects_raw[0]:
            subjects = [s for s in subjects_raw[0].split(',') if s]
        else:
            subjects = [s for s in subjects_raw if s]
    else:
        subjects = []

    filters = {
        'sort': sort,
        'timeframe': timeframe,
        'category': category,
        'broadcasters': broadcasters,
        'themes': themes,
        'subjects': subjects,
        'layout': layout,
        'search': search,
        'liked': liked
    }
    formatted_clips, _ = format_clips(
        page=page,
        sort=sort,
        timeframe=timeframe,
        category=category,
        broadcasters=broadcasters,
        themes=themes,
        subjects=subjects,
        layout=layout,
        search=search,
        liked=liked
    )
    return render_template(
        'main/clip_queue.html',
        title='Clip Queue',
        categories=categories,
        broadcaster_choices=broadcaster_choices,
        theme_choices=theme_choices,
        subject_choices=subject_choices,
        layout_choices=layout_choices,
        subject_categories=subject_categories,
        clips=formatted_clips,
        clip_index=0,
        filters=filters,
        embed_parent=EMBED_PARENT
    )

@bp.route('/clip-queue/filter', methods=['POST'])
def clip_queue_filter():
    sort = request.form.get('sort', 'views')
    timeframe = request.form.get('timeframe', '7d')
    category = request.form.get('category')
    broadcasters = request.form.getlist('broadcasters')
    themes = request.form.getlist('themes')
    subjects = request.form.getlist('subjects')
    layout = request.form.get('layout')
    search = request.form.get('search', '')
    liked = request.form.get('liked', '0') == '1'
    filters = {
        'sort': sort,
        'timeframe': timeframe,
        'category': category,
        'broadcasters': broadcasters,
        'themes': themes,
        'subjects': subjects,
        'layout': layout,
        'search': search,
        'liked': liked
    }
    formatted_clips, has_next = format_clips(
        page=1,
        sort=sort,
        timeframe=timeframe,
        category=category,
        broadcasters=broadcasters,
        themes=themes,
        subjects=subjects,
        layout=layout,
        search=search,
        liked=liked
    )
    return render_template(
        'main/clip_viewer.html',
        clips=formatted_clips,
        clip_index=0,
        filters=filters,
        embed_parent=EMBED_PARENT,
        page=1,
        has_next=has_next
    )

@bp.route('/clip-queue/next', methods=['POST'])
def clip_queue_next():
    clip_index = int(request.form.get('clip_index', 0)) + 1
    page = int(request.form.get('page', 1))
    filters = request.form.get('filters')
    filters = json.loads(filters) if filters else {}
    sort = filters.get('sort', 'views')
    timeframe = filters.get('timeframe', '7d')
    category = filters.get('category')
    broadcasters = filters.get('broadcasters', [])
    themes = filters.get('themes', [])
    subjects = filters.get('subjects', [])
    layout = filters.get('layout')
    search = filters.get('search', '')
    liked = filters.get('liked', False)

    # Load current page
    formatted_clips, has_next = format_clips(
        page=page,
        sort=sort,
        timeframe=timeframe,
        category=category,
        broadcasters=broadcasters,
        themes=themes,
        subjects=subjects,
        layout=layout,
        search=search,
        liked=liked
    )
    if clip_index >= len(formatted_clips):
        if has_next:
            # Load next page
            page += 1
            formatted_clips, has_next = format_clips(
                page=page,
                sort=sort,
                timeframe=timeframe,
                category=category,
                broadcasters=broadcasters,
                themes=themes,
                subjects=subjects,
                layout=layout,
                search=search,
                liked=liked
            )
            clip_index = 0
        else:
            clip_index = len(formatted_clips) - 1 if formatted_clips else 0

    return render_template(
        'main/clip_viewer.html',
        clips=formatted_clips,
        clip_index=clip_index,
        filters=filters,
        embed_parent=EMBED_PARENT,
        page=page,
        has_next=has_next
    )

@bp.route('/clip-queue/prev', methods=['POST'])
def clip_queue_prev():
    clip_index = int(request.form.get('clip_index', 0)) - 1
    page = int(request.form.get('page', 1))
    filters = request.form.get('filters')
    filters = json.loads(filters) if filters else {}
    sort = filters.get('sort', 'views')
    timeframe = filters.get('timeframe', '7d')
    category = filters.get('category')
    broadcasters = filters.get('broadcasters', [])
    themes = filters.get('themes', [])
    subjects = filters.get('subjects', [])
    layout = filters.get('layout')
    search = filters.get('search', '')
    liked = filters.get('liked', False)

    if clip_index < 0 and page > 1:
        # Go to previous page, last clip
        page -= 1
        formatted_clips, has_next = format_clips(
            page=page,
            sort=sort,
            timeframe=timeframe,
            category=category,
            broadcasters=broadcasters,
            themes=themes,
            subjects=subjects,
            layout=layout,
            search=search,
            liked=liked
        )
        clip_index = len(formatted_clips) - 1
    else:
        formatted_clips, has_next = format_clips(
            page=page,
            sort=sort,
            timeframe=timeframe,
            category=category,
            broadcasters=broadcasters,
            themes=themes,
            subjects=subjects,
            layout=layout,
            search=search,
            liked=liked
        )
        if clip_index < 0:
            clip_index = 0

    return render_template(
        'main/clip_viewer.html',
        clips=formatted_clips,
        clip_index=clip_index,
        filters=filters,
        embed_parent=EMBED_PARENT,
        page=page,
        has_next=has_next
    )