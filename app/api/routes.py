from flask import current_app, render_template, jsonify, request, redirect, url_for, flash
from flask_login import current_user, login_required
from werkzeug.security import generate_password_hash
from datetime import datetime as dt, timedelta, timezone
from app.api import bp
from decorators import require_api_key, rank_required
from app.models import *
from app.dash.forms import deleteForm
from sqlalchemy import func
import json, random, secrets, subprocess

@bp.context_processor
def inject_sidebar_labels():
    sidebar_labels = Status.query.order_by('id')
    return dict(sidebar=sidebar_labels)

def get_git_revision_hash():
    try:
        return subprocess.check_output(['git', 'rev-parse', '--short', 'HEAD'], cwd=current_app.root_path).strip().decode('ascii')
    except (subprocess.CalledProcessError, FileNotFoundError):
        return 'Unknown'

@bp.context_processor
def inject_commit_version():
    commit_version = get_git_revision_hash()
    return dict(commit_version=commit_version)

@bp.route('/api/generate_key', methods=['POST'])
@rank_required('SUPERADMIN', 'ADMIN')
def generate_api_key():
    lookup_id = secrets.token_hex(6)
    api_key = secrets.token_hex(24)
    full_key = f'sk_{lookup_id}_{api_key}'
    payload = request.get_json(silent=True) or request.form
    name = payload.get('name', 'Unnamed Key')

    existing_name = ApiKey.query.filter_by(name=name).first()
    if existing_name:
        return jsonify({'error': 'API key name already exists.'}), 400
    
    new_key = ApiKey(
        key_id=lookup_id,
        key_hash=generate_password_hash(api_key),
        name=name,
        uses=0,
        created_by=current_user.id,
        created_at=datetime.now(timezone.utc)
    )
    db.session.add(new_key)
    db.session.commit()

    if request.headers.get('HX-Request') != 'true':
        return jsonify({'api_key': full_key}), 201

    api_keys = ApiKey.query.all() if current_user.rank.name == 'SUPERADMIN' else ApiKey.query.filter_by(created_by=current_user.id).all()
    return render_template('dash/api/_api_keys_table_body.html', api_keys=api_keys), 201, {
        'HX-Trigger': json.dumps({'showApiKey': {'api_key': full_key}})
    }

@bp.route('/api/manage', methods=['GET'])
@login_required
@rank_required('SUPERADMIN', 'ADMIN')
def api_manage():
    user_rank = current_user.rank.name
    if user_rank == 'SUPERADMIN':
        api_keys = ApiKey.query.all()
    else:
        api_keys = ApiKey.query.filter_by(created_by=current_user.id).all()

    columns = {
        'name': 'Name',
        'uses': 'Uses',
        'created_by': 'Created By',
        'created_at': 'Created At'
    }
    return render_template('dash/api/api_keys.html', api_keys=api_keys, columns=columns)

@bp.route('/api/manage/<id>/delete', methods=['GET', 'POST'])
@login_required
@rank_required('SUPERADMIN', 'ADMIN')
def api_delete(id):
    api_key = ApiKey.query.filter(ApiKey.id == id).first()
    if api_key != None:
        if current_user.rank.name != 'SUPERADMIN' and api_key.created_by != current_user.id:
            return redirect(url_for('api.api_manage')), 403
        form = deleteForm()
    else:
        return redirect(url_for('api.api_manage')), 404

    if request.method == 'POST':
        if form.cancel.data:
            return redirect(url_for('api.api_manage'))
    if form.validate_on_submit():
        if form.name.data != api_key.name:
            flash('Entered name does not match!', 'form-error')
        else:
            db.session.delete(api_key)
            db.session.commit()
            return redirect(url_for('api.api_manage'))
    return render_template('dash/api/api_delete.html', title='Delete API Key', form=form, api_key=api_key)

@bp.route('/api/manage/test', methods=['GET'])
@login_required
@rank_required('SUPERADMIN', 'ADMIN')
def api_test():
    api_endpoints = [
        {
            'path': '/api/get-categories',
            'description': 'List all clip categories.',
            'parameters': [],
        },
        {
            'path': '/api/get-themes',
            'description': 'List all clip themes.',
            'parameters': [],
        },
        {
            'path': '/api/get-subjects',
            'description': 'List all clip subjects.',
            'parameters': [],
        },
        {
            'path': '/api/get-statuses',
            'description': 'List all clip statuses.',
            'parameters': [],
        },
        {
            'path': '/api/get-layouts',
            'description': 'List all clip layouts.',
            'parameters': [],
        },
        {
            'path': '/api/get-clips',
            'description': 'Search and paginate visible clips.',
            'parameters': [
                {'name': 'category_id', 'description': 'Filter by category ID'},
                {'name': 'theme_ids', 'description': 'Comma-separated theme IDs'},
                {'name': 'theme_filter', 'description': 'Use "and" or "or" for theme_ids'},
                {'name': 'subject_ids', 'description': 'Comma-separated subject IDs'},
                {'name': 'subject_filter', 'description': 'Use "and" or "or" for subject_ids'},
                {'name': 'status_id', 'description': 'Filter by status ID (excluding hidden statuses)'},
                {'name': 'broadcaster_ids', 'description': 'Comma-separated broadcaster IDs'},
                {'name': 'sort', 'description': 'Sort by new, old, views, or random'},
                {'name': 'page', 'description': 'Page number, starting at 1'},
                {'name': 'timeframe', 'description': '24h, 7d, 30d, 1y, or custom:start|end'},
                {'name': 'seed', 'description': 'Optional seed for deterministic ordering'},
            ],
        },
    ]
    return render_template('dash/api/api_test.html', title='API Reference', api_endpoints=api_endpoints)

@bp.route('/api/manage/test/request', methods=['POST'])
@login_required
@rank_required('SUPERADMIN', 'ADMIN')
def api_test_request():
    endpoint_paths = {
        '/api/get-categories',
        '/api/get-themes',
        '/api/get-subjects',
        '/api/get-statuses',
        '/api/get-layouts',
        '/api/get-clips',
    }
    endpoint = request.form.get('endpoint', '')
    api_key = request.form.get('api_key', '').strip()
    query_params = {}

    for line in request.form.get('query_params', '').splitlines():
        name, separator, value = line.partition('=')
        if separator and name.strip():
            query_params[name.strip()] = value.strip()

    if endpoint not in endpoint_paths:
        return render_template('dash/api/_api_response.html', response_status='400 Bad Request', response_body='Unknown endpoint.')
    if not api_key:
        return render_template('dash/api/_api_response.html', response_status='400 Bad Request', response_body='An API key is required.')

    response = current_app.test_client().get(
        endpoint,
        query_string=query_params,
        headers={'Authorization': f'Bearer {api_key}'},
    )
    response_body = response.get_data(as_text=True)
    try:
        response_body = json.dumps(json.loads(response_body), indent=2)
    except (TypeError, ValueError):
        pass

    response_status = f'{response.status_code} {response.status}'
    return render_template(
        'dash/api/_api_response.html',
        response_status=response_status,
        response_body=response_body or '(empty response)',
    )

# 
# 
# 
# 
# API Endpoints
# 
# 
# 
#
@bp.route('/api/get-categories', methods=['GET'])
@require_api_key
def get_categories():
    try:
        page = max(request.args.get('page', 1, type=int), 1)
        per_page = 100
        categories = Category.query.paginate(page=page, per_page=per_page, error_out=False)
        category_list = [{
            'id': category.id,
            'name': category.name
        } for category in categories]
        return jsonify({
            'total': categories.total,
            'page': page,
            'per_page': per_page,
            'has_next': categories.has_next,
            'categories': category_list
        }), 200
    except Exception as e:
        return jsonify({'error': 'An error occurred while fetching categories'}), 500

@bp.route('/api/get-themes', methods=['GET'])
@require_api_key
def get_themes():
    try:
        page = max(request.args.get('page', 1, type=int), 1)
        per_page = 100
        themes = Theme.query.paginate(page=page, per_page=per_page, error_out=False)
        theme_list = [{
            'id': theme.id,
            'name': theme.name
        } for theme in themes]
        return jsonify({
            'total': themes.total,
            'page': page,
            'per_page': per_page,
            'has_next': themes.has_next,
            'themes': theme_list
        }), 200
    except Exception as e:
        return jsonify({'error': 'An error occurred while fetching themes'}), 500

@bp.route('/api/get-subjects', methods=['GET'])
@require_api_key
def get_subjects():
    try:
        page = max(request.args.get('page', 1, type=int), 1)
        per_page = 100
        subjects = Subject.query.paginate(page=page, per_page=per_page, error_out=False)
        subject_list = [{
            'id': subject.id, 
            'name': subject.name
        } for subject in subjects]
        return jsonify({
            'total': subjects.total,
            'page': page,
            'per_page': per_page,
            'has_next': subjects.has_next,
            'subjects': subject_list
        }), 200
    except Exception as e:
        return jsonify({'error': 'An error occurred while fetching subjects'}), 500

@bp.route('/api/get-statuses', methods=['GET'])
@require_api_key
def get_statuses():
    try:
        page = max(request.args.get('page', 1, type=int), 1)
        per_page = 100
        statuses = Status.query.paginate(page=page, per_page=per_page, error_out=False)
        status_list = [{
            'id': status.id, 
            'name': status.name,
            'type': status.type
        } for status in statuses]
        return jsonify({
            'total': statuses.total,
            'page': page,
            'per_page': per_page,
            'has_next': statuses.has_next,
            'statuses': status_list
        }), 200
    except Exception as e:
        return jsonify({'error': 'An error occurred while fetching statuses'}), 500

@bp.route('/api/get-layouts', methods=['GET'])
@require_api_key
def get_layouts():
    try:
        page = max(request.args.get('page', 1, type=int), 1)
        per_page = 100
        layouts = Layout.query.paginate(page=page, per_page=per_page, error_out=False)
        layout_json = [{
            'id': layout.id, 
            'name': layout.name
        } for layout in layouts]
        has_next = layouts.has_next
        
        return jsonify({
            'total': layouts.total,
            'page': page,
            'per_page': per_page,
            'has_next': has_next,
            'layouts': layout_json
        }), 200
    except Exception as e:
        return jsonify({'error': 'An error occurred while fetching layouts'}), 500

@bp.route('/api/get-clips', methods=['GET'])
@require_api_key
def get_clips():
    try:
        def get_ids(name):
            values = []
            for value in request.args.getlist(name):
                values.extend(value.split(','))
            return [int(value) for value in values if value.strip().isdigit()]

        category_id = request.args.get('category_id', type=int)
        theme_ids = get_ids('theme_ids')
        theme_filter_mode = request.args.get('theme_filter', 'or').lower()
        subject_ids = get_ids('subject_ids')
        subject_filter_mode = request.args.get('subject_filter', 'or').lower()
        status_id = request.args.get('status_id', type=int)
        sort = request.args.get('sort', 'random').lower()
        page = max(request.args.get('page', 1, type=int), 1)
        timeframe = request.args.get('timeframe', 'all').lower()
        broadcaster_ids = get_ids('broadcaster_ids')
        seed = request.args.get('seed', random.randint(0, 1_000_000), type=int)

        filters = []
        if category_id is not None:
            filters.append(Clip.category_id == category_id)
        if status_id is not None:
            filters.append(Clip.status_id == status_id)

        if theme_ids:
            if theme_filter_mode == 'and':
                for theme_id in theme_ids:
                    filters.append(Clip.themes.any(Theme.id == theme_id))
            else:
                filters.append(Clip.themes.any(Theme.id.in_(theme_ids)))

        if subject_ids:
            if subject_filter_mode == 'and':
                for subject_id in subject_ids:
                    filters.append(Clip.subjects.any(Subject.id == subject_id))
            else:
                filters.append(Clip.subjects.any(Subject.id.in_(subject_ids)))

        if broadcaster_ids:
            filters.append(Clip.broadcaster_id.in_(broadcaster_ids))

        now = dt.now(timezone.utc)
        timeframe_days = {'24h': 1, '7d': 7, '30d': 30, '1y': 365}.get(timeframe)
        if timeframe_days:
            filters.append(Clip.created_at >= now - timedelta(days=timeframe_days))
        elif timeframe.startswith('custom:'):
            try:
                date_range = timeframe.split(':', 1)[1]
                start_str, end_str = date_range.split('|')
                start_date = dt.strptime(start_str, '%Y-%m-%d').replace(tzinfo=timezone.utc)
                end_date = dt.strptime(end_str, '%Y-%m-%d').replace(tzinfo=timezone.utc) + timedelta(days=1)
                filters.append(Clip.created_at >= start_date)
                filters.append(Clip.created_at < end_date)
            except (ValueError, IndexError):
                pass

        filters.append(Clip.is_available_in_clip_player == True)

        filters.append(Clip.status.has(Status.type != 'hidden'))

        order_by = {
            'new': Clip.created_at.desc(),
            'old': Clip.created_at.asc(),
            'views': Clip.view_count.desc(),
            'random': func.rand(seed)
        }.get(sort, Clip.view_count.desc())
        per_page = 100
        clips = Clip.query.filter(*filters).order_by(order_by).paginate(page=page, per_page=per_page, error_out=False)

        clips_json = [{
            'twitch_id': clip.twitch_id,
            'url': clip.url,
            'embed_url': clip.embed_url,
            'broadcaster': {
                'name': clip.broadcaster_name,
                'id': clip.broadcaster_id
            },
            'creator_name': clip.creator_name,
            'title': clip.title,
            'title_override': clip.title_override,
            'view_count': clip.view_count,
            'created_at': clip.created_at,
            'thumbnail_url': clip.thumbnail_url,
            'duration': clip.duration,
            'is_available_in_clip_player': clip.is_available_in_clip_player,
            'category': {
                'name': clip.category.name if clip.category else None,
                'id': clip.category_id
            },
            'status': {
                'name': clip.status.name if clip.status else None,
                'id': clip.status_id
            },
            'layout': {
                'name': clip.layout.name if clip.layout else None,
                'id': clip.layout_id
            },
            'subjects': [
                {
                    'name': subject.name if subject else None,
                    'id': subject.id
                }
                for subject in clip.subjects
            ],
            'themes': [
                {
                    'name': theme.name if theme else None,
                    'id': theme.id
                }
                for theme in clip.themes
            ]
        } for clip in clips]
        has_next = clips.has_next

        return jsonify({
            'total': clips.total,
            'page': page,
            'per_page': per_page,
            'has_next': has_next,
            'seed': seed,
            'clips': clips_json
        }), 200
    except Exception as e:
        return jsonify({'error': 'An error occurred while fetching clips'}), 500