from flask import render_template, flash, redirect, url_for, request, session
import math
from datetime import datetime, timezone
from flask_login import current_user, login_required
from app.main import bp
from dotenv import load_dotenv
from decorators import rank_required
from app.models import *
from sqlalchemy import or_
from app.dash.forms import *

load_dotenv()

def set_session_filters(route, page=1, size=20, order='asc', sort='id', search=''):
    session[route] = {
        'page': page,
        'size': size,
        'order': order,
        'sort': sort,
        'search': search
    }

def get_session_filters(route):
    if route in session:
        return session[route]
    
def get_value(request_value, session_value, default):
    if request_value is not None:
        return request_value
    if session_value is not None:
        return session_value
    return default

# ? Unsure of if this will be kept, this would help with page updates without refresh 
@bp.route('/load_table', methods=['POST'])
@login_required
@rank_required('SUPERADMIN', 'ADMIN', 'MODERATOR')
def load_table():
    page = request.args.get('page', 1, type=int)
    size = request.args.get('size', 3, type=int)
    order = request.args.get('order', 'asc', type=str)
    sort = request.args.get('sort', 'id', type=str)
    search = request.args.get('search', '', type=str)
    set_session_filters('test', page, size, order, sort, search)
    query = Status.query.order_by('id')
    status_labels = db.paginate(query, page=page, per_page=size, error_out=False)
    pages = list(status_labels.iter_pages(left_edge=2, left_current=1, right_edge=2, right_current=1))
    # Convert the status labels to a list of dictionaries
    status_labels_list = [label.to_dict() for label in status_labels.items]
    
    return {
        'status_labels': status_labels_list,
        'page': page,
        'pages': pages,
        'size': size,
        'first': status_labels.first,
        'last': status_labels.last,
        'total': status_labels.total,
        'order': order,
        'sort': sort,
        'search': search
    }

# 
# 
# 
# 
# Dashboard
# 
# 
# 
#
@bp.route('/dashboard')
@login_required
@rank_required('SUPERADMIN', 'ADMIN', 'MODERATOR')
def dashboard():
    sidebar_labels = Status.query.order_by('id')
    unsorted = Clip.query.filter(or_(Clip.category_id == None, Clip.themes == None, Clip.subjects == None)).count()
    return render_template('dash/dashboard.html', title='Dashboard', sidebar=sidebar_labels, unsorted=unsorted)
    
# 
# 
# 
# 
# Clips
# 
# 
# 
#
@bp.route('/dashboard/clips')
@login_required
@rank_required('SUPERADMIN', 'ADMIN', 'MODERATOR')
def dash_clips():
    filters = get_session_filters('clips')
    page = get_value(request.args.get('page', type=int), filters.get('page') if filters else None, 1)
    size = get_value(request.args.get('size', type=int), filters.get('size') if filters else None, 20)
    order = get_value(request.args.get('order', type=str), filters.get('order') if filters else None, 'asc')
    sort = get_value(request.args.get('sort', type=str), filters.get('sort') if filters else None, 'id')
    search = get_value(request.args.get('search', type=str), filters.get('search') if filters else None, '')
    set_session_filters('clips', page, size, order, sort, search)
    columns = {
        'id': 'ID',
        'twitch_id': 'Twitch ID',
        'broadcaster_name': 'Broadcaster',
        'creator_name': 'Creator',
        'title': 'Title',
        'title_override': 'Title Override',
        'view_count': 'Views',
        'created_at': 'Created At',
        'updated_by': 'Updated By',
        'updated_at': 'Updated At',
        'duration': 'Duration',
        'notes': 'Notes',
        'category': 'Category',
        'status': 'Status',
        'themes': 'Themes',
        'subjects': 'Subjects',
    }
    # Make sure the sort input is valid
    if sort in columns.keys():
        if sort == 'clips':
            query = Clip.query.outerjoin(Clip, Clip.twitch_id == Clip.creator_id).group_by(Clip.twitch_id).filter(
                or_(
                    Clip.twitch_id.ilike(f'%{search}%'),
                    Clip.broadcaster_name.ilike(f'%{search}%'),
                    Clip.creator_name.ilike(f'%{search}%'),
                    Clip.title.ilike(f'%{search}%'),
                    Clip.title_override.ilike(f'%{search}%'),
                    Clip.notes.ilike(f'%{search}%'),
                    # Clip.category.ilike(f'%{search}%'),
                    # Clip.status.ilike(f'%{search}%'),
                    # Clip.themes.ilike(f'%{search}%'),
                    # Clip.subjects.ilike(f'%{search}%')
                )
            ).order_by(db.func.count(Clip.id).desc() if order == 'desc' else db.func.count(Clip.id).asc())
        elif sort == 'rank':
            query = Clip.query.outerjoin(Rank, Clip.rank_id == Rank.id).filter(
                or_(
                    Clip.twitch_id.ilike(f'%{search}%'),
                    Clip.broadcaster_name.ilike(f'%{search}%'),
                    Clip.creator_name.ilike(f'%{search}%'),
                    Clip.title.ilike(f'%{search}%'),
                    Clip.title_override.ilike(f'%{search}%'),
                    Clip.notes.ilike(f'%{search}%'),
                    # Clip.category.ilike(f'%{search}%'),
                    # Clip.status.ilike(f'%{search}%'),
                    # Clip.themes.ilike(f'%{search}%'),
                    # Clip.subjects.ilike(f'%{search}%')
                )
            ).order_by(Rank.id.desc() if order == 'desc' else Rank.id.asc())
        else:
            query = Clip.query.filter(
                or_(
                    Clip.twitch_id.ilike(f'%{search}%'),
                    Clip.broadcaster_name.ilike(f'%{search}%'),
                    Clip.creator_name.ilike(f'%{search}%'),
                    Clip.title.ilike(f'%{search}%'),
                    Clip.title_override.ilike(f'%{search}%'),
                    Clip.notes.ilike(f'%{search}%'),
                    # Clip.category.ilike(f'%{search}%'),
                    # Clip.status.ilike(f'%{search}%'),
                    # Clip.themes.ilike(f'%{search}%'),
                    # Clip.subjects.ilike(f'%{search}%')
                )
            ).order_by(getattr(Clip, sort).desc() if order == 'desc' else getattr(Clip, sort).asc())
    else:
        # Default to sort by id
        query = Clip.query.filter(
            or_(
                Clip.twitch_id.ilike(f'%{search}%'),
                Clip.broadcaster_name.ilike(f'%{search}%'),
                Clip.creator_name.ilike(f'%{search}%'),
                Clip.title.ilike(f'%{search}%'),
                Clip.title_override.ilike(f'%{search}%'),
                Clip.notes.ilike(f'%{search}%'),
                # Clip.category.ilike(f'%{search}%'),
                # Clip.status.ilike(f'%{search}%'),
                # Clip.themes.ilike(f'%{search}%'),
                # Clip.subjects.ilike(f'%{search}%')
            )
        ).order_by(Clip.id.desc() if order == 'desc' else Clip.id.asc())
    # Default to page 1 if page number isn't valid
    if page > math.ceil(query.count()/size) or page < 1:
        page = 1
    clips = db.paginate(query, page=page, per_page=size, error_out=False)
    pages = clips.iter_pages(left_edge=2, left_current=1, right_edge=2, right_current=1)
    sidebar_labels = Status.query.order_by('id')
    return render_template('dash/clips/clips.html', title='Dashboard - Clips', sidebar=sidebar_labels, clips=clips, page=page, pages=pages, size=size, order=order, sort=sort, search=search, columns=columns)
    
@bp.route('/dashboard/clips/<id>/edit', methods=['GET', 'POST'])
@login_required
@rank_required('SUPERADMIN', 'ADMIN', 'MODERATOR')
def dash_clips_edit(id):
    current_clip = Clip.query.filter(Clip.id == id).first()
    current_clip_info = []
    if current_clip != None:
        current_clip_info = [current_clip.title_override, 
                            current_clip.notes,
                            current_clip.category_id,
                            current_clip.status_id,
                            [theme.id for theme in current_clip.themes],
                            [subject.id for subject in current_clip.subjects]]
        # populate the form with the existing data
        form = clipForm(title_override=current_clip.title_override, 
                        notes=current_clip.notes,
                        category=current_clip.category_id,
                        status=current_clip.status_id,
                        themes=[theme.id for theme in current_clip.themes],
                        subjects=[subject.id for subject in current_clip.subjects])
        form.category.choices = [(c.id, c.name) for c in Category.query.order_by('id')]
        form.status.choices = [(st.id, st.name) for st in Status.query.order_by('id')]
        form.themes.choices = [(t.id, t.name) for t in Theme.query.order_by('id')]
        form.subjects.choices = []
        form.subjects.option_attrs = {}

        for sc in SubjectCategory.query.order_by('id'):
            subjects = Subject.query.filter(Subject.category_id == sc.id).order_by('id').all()
            if not subjects:
                continue

            group_choices = []
            for su in subjects:
                group_choices.append((su.id, su.name))
                form.subjects.option_attrs[str(su.id)] = {
                    'data-subtext': su.subtext or '',
                    'data-tokens': su.keywords or ''
                }

            form.subjects.choices.append((sc.name, group_choices))
    else:
        return redirect(url_for('main.dash_clips'))
    
    sidebar_labels = Status.query.order_by('id')

    if request.method == 'POST':
        if form.cancel.data:
            return redirect(url_for('main.dash_clips'))
    if form.validate_on_submit():
        form_info = [form.title_override.data, 
                     form.notes.data,
                     form.category.data,
                     form.status.data,
                     form.themes.data,
                     form.subjects.data] # list to compare with current_clip_info
        # if the form data hasn't changed, just redirect to clips page
        if form_info == current_clip_info:
            return redirect(url_for('main.dash_clips'))
        # otherwise handle changes
        else:
            if current_clip.updated_by != int(current_user.twitch_id):
                curr_user = User.query.filter(User.id == current_user.id).first()
                curr_user.contributions += 1
                db.session.commit()
            current_clip.title_override = form.title_override.data
            current_clip.notes = form.notes.data
            current_clip.category_id = form.category.data
            current_clip.status_id = form.status.data
            current_clip.themes = [Theme.query.get(theme_id) for theme_id in form.themes.data]
            current_clip.subjects = [Subject.query.get(subject_id) for subject_id in form.subjects.data]
            current_clip.updated_by = current_user.twitch_id
            current_clip.updated_at = datetime.now(timezone.utc)
            db.session.commit()
            return redirect(url_for('main.dash_clips'))
    return render_template('dash/clips/edit_clip.html', title='Dashboard - Edit Clip', sidebar=sidebar_labels, form=form, clip=current_clip)

@bp.route('/dashboard/clips/<id>/delete', methods=['GET', 'POST'])
@login_required
@rank_required('SUPERADMIN', 'ADMIN')
def dash_clips_delete(id):
    clip = Clip.query.filter(Clip.id == id).first()
    if clip != None:
        form = deleteForm()
    else:
        return redirect(url_for('main.dash_clips'))
    
    sidebar_labels = Status.query.order_by('id')

    if request.method == 'POST':
        if form.cancel.data:
            return redirect(url_for('main.dash_clips'))
    if form.validate_on_submit():
        # TODO: add more validation to prevent deletion of clips
        # if the entered name doesn't match the clip name, prompt an error
        if form.name.data != clip.display_name:
            flash('Entered name does not match!', 'form-error')
        # clip name confirmed, delete clip
        else:
            db.session.delete(clip)
            db.session.commit()
            return redirect(url_for('main.dash_clips'))
    return render_template('dash/clips/delete_clip.html', title='Dashboard - Delete Clip', sidebar=sidebar_labels, form=form, clip=clip)
    
# 
# 
# 
# 
# Users
# 
# 
# 
#
@bp.route('/dashboard/users')
@login_required
@rank_required('SUPERADMIN', 'ADMIN', 'MODERATOR')
def dash_users():
    filters = get_session_filters('users')
    page = get_value(request.args.get('page', type=int), filters.get('page') if filters else None, 1)
    size = get_value(request.args.get('size', type=int), filters.get('size') if filters else None, 20)
    order = get_value(request.args.get('order', type=str), filters.get('order') if filters else None, 'asc')
    sort = get_value(request.args.get('sort', type=str), filters.get('sort') if filters else None, 'id')
    search = get_value(request.args.get('search', type=str), filters.get('search') if filters else None, '')
    set_session_filters('users', page, size, order, sort, search)
    columns = {
        'id': 'ID',
        'twitch_id': 'Twitch ID',
        'display_name': 'Name',
        'contributions': 'Contributions',
        'clips': 'Clips',
        'notes': 'Notes',
        'rank': 'Rank',
        'login_enabled': 'Login Enabled',
        'updated_by': 'Updated By',
        'updated_at': 'Updated At'
    }
    # Make sure the sort input is valid
    if sort in columns.keys():
        # Sorting by clip count requires joining Clip and User tables
        if sort == 'clips':
            query = User.query.outerjoin(Clip, User.twitch_id == Clip.creator_id).group_by(User.twitch_id).filter(
                or_(
                    User.twitch_id.ilike(f'%{search}%'),
                    User.display_name.ilike(f'%{search}%'),
                    User.notes.ilike(f'%{search}%'),
                    User.login_enabled.ilike(f'%{search}%')
                )
            ).order_by(db.func.count(Clip.id).desc() if order == 'desc' else db.func.count(Clip.id).asc())
        elif sort == 'rank':
            query = User.query.outerjoin(Rank, User.rank_id == Rank.id).filter(
                or_(
                    User.twitch_id.ilike(f'%{search}%'),
                    User.display_name.ilike(f'%{search}%'),
                    User.notes.ilike(f'%{search}%'),
                    User.login_enabled.ilike(f'%{search}%')
                )
            ).order_by(Rank.id.desc() if order == 'desc' else Rank.id.asc())
        else:
            query = User.query.filter(
                or_(
                    User.twitch_id.ilike(f'%{search}%'),
                    User.display_name.ilike(f'%{search}%'),
                    User.notes.ilike(f'%{search}%'),
                    User.login_enabled.ilike(f'%{search}%')
                )
            ).order_by(getattr(User, sort).desc() if order == 'desc' else getattr(User, sort).asc())
    else:
        # Default to sort by id
        query = User.query.filter(
            or_(
                User.twitch_id.ilike(f'%{search}%'),
                User.display_name.ilike(f'%{search}%'),
                User.notes.ilike(f'%{search}%'),
                User.login_enabled.ilike(f'%{search}%')
            )
        ).order_by(User.id.desc() if order == 'desc' else User.id.asc())
    # Default to page 1 if page number isn't valid
    if page > math.ceil(query.count()/size) or page < 1:
        page = 1
    users = db.paginate(query, page=page, per_page=size, error_out=False)
    pages = users.iter_pages(left_edge=2, left_current=1, right_edge=2, right_current=1)
    sidebar_labels = Status.query.order_by('id')
    return render_template('dash/users/users.html', title='Dashboard - Users', sidebar=sidebar_labels, users=users, page=page, pages=pages, size=size, order=order, sort=sort, search=search, columns=columns)
    
@bp.route('/dashboard/users/<id>/edit', methods=['GET', 'POST'])
@login_required
@rank_required('SUPERADMIN', 'ADMIN')
def dash_users_edit(id):
    curr_user = User.query.filter(User.id == id).first()
    curr_user_info = []
    if curr_user != None:
        curr_user_info = [curr_user.rank.id, curr_user.contributions, curr_user.login_enabled, curr_user.notes] # list to compare to for edits
        # populate the form with the existing data
        form = userForm(rank=curr_user.rank_id, contributions=curr_user.contributions, enabled=curr_user.login_enabled, notes=curr_user.notes)
        form.rank.choices = [(r.id, r.name) for r in Rank.query.order_by('id')]
    else:
        return redirect(url_for('main.dash_users'))
    
    sidebar_labels = Status.query.order_by('id')

    if request.method == 'POST':
        if form.cancel.data:
            return redirect(url_for('main.dash_users'))
    if form.validate_on_submit():
        form_info = [form.rank.data, form.contributions.data, form.enabled.data, form.notes.data] # list to compare with curr_user_info
        # if the form data hasn't changed, just redirect to users page
        if form_info == curr_user_info:
            return redirect(url_for('main.dash_users'))
        # otherwise handle changes
        else:
            curr_user.rank_id = form.rank.data
            curr_user.contributions = form.contributions.data
            curr_user.login_enabled = form.enabled.data
            curr_user.notes = form.notes.data
            curr_user.updated_by = current_user.twitch_id
            curr_user.updated_at = datetime.now(timezone.utc)
            db.session.commit()
            return redirect(url_for('main.dash_users'))
    return render_template('dash/users/edit_user.html', title='Dashboard - Edit User', sidebar=sidebar_labels, form=form)

@bp.route('/dashboard/users/<id>/delete', methods=['GET', 'POST'])
@login_required
@rank_required('SUPERADMIN')
def dash_users_delete(id):
    user = User.query.filter(User.id == id).first()
    if user != None:
        form = deleteForm()
    else:
        return redirect(url_for('main.dash_users'))
    
    sidebar_labels = Status.query.order_by('id')

    if request.method == 'POST':
        if form.cancel.data:
            return redirect(url_for('main.dash_users'))
    if form.validate_on_submit():
        # if the entered name doesn't match the user name, prompt an error
        if form.name.data != user.display_name:
            flash('Entered name does not match!', 'form-error')
        # user name confirmed, delete user
        else:
            db.session.delete(user)
            db.session.commit()
            return redirect(url_for('main.dash_users'))
    return render_template('dash/users/delete_user.html', title='Dashboard - Delete User', sidebar=sidebar_labels, form=form, user=user)

# 
# 
# 
# 
# Categories
# 
# 
# 
#
@bp.route('/dashboard/categories')
@login_required
@rank_required('SUPERADMIN', 'ADMIN', 'MODERATOR')
def dash_categories():
    filters = get_session_filters('categories')
    page = get_value(request.args.get('page', type=int), filters.get('page') if filters else None, 1)
    size = get_value(request.args.get('size', type=int), filters.get('size') if filters else None, 20)
    order = get_value(request.args.get('order', type=str), filters.get('order') if filters else None, 'asc')
    sort = get_value(request.args.get('sort', type=str), filters.get('sort') if filters else None, 'id')
    search = get_value(request.args.get('search', type=str), filters.get('search') if filters else None, '')
    set_session_filters('categories', page, size, order, sort, search)
    columns = {
        'id': 'ID',
        'name': 'Name',
        'clips': 'Clips',
        'notes': 'Notes',
        'created_by': 'Created By',
        'created_at': 'Created At',
        'updated_by': 'Updated By',
        'updated_at': 'Updated At'
    }
    # Make sure the sort input is valid
    if sort in columns.keys():
        # Sorting by clip count requires joining Clip and Category tables
        if sort == 'clips':
            query = Category.query.outerjoin(Clip, Category.id == Clip.category_id).group_by(Category.id).filter(
                or_(
                    Category.id.ilike(f'%{search}%'),
                    Category.name.ilike(f'%{search}%'),
                    Category.notes.ilike(f'%{search}%'),
                    Category.created_by.ilike(f'%{search}%'),
                    Category.created_at.ilike(f'%{search}%'),
                    Category.updated_at.ilike(f'%{search}%')
                )
            ).order_by(db.func.count(Clip.id).desc() if order == 'desc' else db.func.count(Clip.id).asc())
        else:
            query = Category.query.filter(
                or_(
                    Category.id.ilike(f'%{search}%'),
                    Category.name.ilike(f'%{search}%'),
                    Category.notes.ilike(f'%{search}%'),
                    Category.created_by.ilike(f'%{search}%'),
                    Category.created_at.ilike(f'%{search}%'),
                    Category.updated_at.ilike(f'%{search}%')
                )
            ).order_by(getattr(Category, sort).desc() if order == 'desc' else getattr(Category, sort).asc())
    else:
        # Default to sort by id
        query = Category.query.filter(
            or_(
                Category.id.ilike(f'%{search}%'),
                Category.name.ilike(f'%{search}%'),
                Category.notes.ilike(f'%{search}%'),
                Category.created_by.ilike(f'%{search}%'),
                Category.created_at.ilike(f'%{search}%'),
                Category.updated_at.ilike(f'%{search}%')
            )
        ).order_by(Category.id.desc() if order == 'desc' else Category.id.asc())
    # Default to page 1 if page number isn't valid
    if page > math.ceil(query.count()/size) or page < 1:
        page = 1
    categories = db.paginate(query, page=page, per_page=size, error_out=False)
    pages = categories.iter_pages(left_edge=2, left_current=1, right_edge=2, right_current=1)
    sidebar_labels = Status.query.order_by('id')
    return render_template('dash/categories/categories.html', title='Dashboard - Categories', sidebar=sidebar_labels, categories=categories, page=page, pages=pages, size=size, order=order, sort=sort, search=search, columns=columns)

@bp.route('/dashboard/categories/create', methods=['GET', 'POST'])
@login_required
@rank_required('SUPERADMIN', 'ADMIN', 'MODERATOR')
def dash_categories_create():
    form = categoryForm()
    sidebar_labels = Status.query.order_by('id')
    if request.method == 'POST':
        if form.cancel.data:
            return redirect(url_for('main.dash_categories'))
    if form.validate_on_submit():
        category = Category.query.filter(Category.name.ilike(form.name.data)).first()
        # category doesn't already exist, create it
        if category is None:
            category = Category(name=form.name.data,
                                notes=form.notes.data,
                                created_at=datetime.now(timezone.utc),
                                updated_at=datetime.now(timezone.utc),
                                created_by=current_user.twitch_id,
                                updated_by=current_user.twitch_id)
            db.session.add(category)
            db.session.commit()
            return redirect(url_for('main.dash_categories'))
        # category already exists, prompt name change
        else:
            flash('Name must be unique!', 'form-error')
    return render_template('dash/categories/create_category.html', title='Dashboard - Create Category', sidebar=sidebar_labels, form=form)
    
@bp.route('/dashboard/categories/<id>/edit', methods=['GET', 'POST'])
@login_required
@rank_required('SUPERADMIN', 'ADMIN', 'MODERATOR')
def dash_categories_edit(id):
    current_category = Category.query.filter(Category.id == id).first()
    current_category_info = []
    if current_category != None:
        current_category_info = [current_category.name, current_category.notes] # list to compare to for edits
        # populate the form with the existing data
        form = categoryForm(name=current_category.name, notes=current_category.notes)
    else:
        return redirect(url_for('main.dash_categories'))
    
    sidebar_labels = Status.query.order_by('id')

    if request.method == 'POST':
        if form.cancel.data:
            return redirect(url_for('main.dash_categories'))
    if form.validate_on_submit():
        form_info = [form.name.data, form.notes.data] # list to compare with current_category_info
        # if the form data hasn't changed, just redirect to categories page
        if form_info == current_category_info:
            return redirect(url_for('main.dash_categories'))
        # otherwise handle changes
        else:
            category = Category.query.filter(Category.name.ilike(form.name.data)).first()
            # category doesn't already exist or is the current category, allow edit
            if category is None or category.name == current_category.name:
                current_category.name = form.name.data
                current_category.notes = form.notes.data
                current_category.updated_by = current_user.twitch_id
                current_category.updated_at = datetime.now(timezone.utc)
                db.session.commit()
                return redirect(url_for('main.dash_categories'))
            # category already exists, prompt name change
            else:
                flash('Name must be unique!', 'form-error')
    return render_template('dash/categories/edit_category.html', title='Dashboard - Edit Category', sidebar=sidebar_labels, form=form)

@bp.route('/dashboard/categories/<id>/delete', methods=['GET', 'POST'])
@login_required
@rank_required('SUPERADMIN', 'ADMIN')
def dash_categories_delete(id):
    category = Category.query.filter(Category.id == id).first()
    if category != None:
        if len(category.clips) > 0:
            # Don't allow deletion of categories with clips assigned
            return redirect(url_for('main.dash_categories'))
        form = deleteForm()
    else:
        return redirect(url_for('main.dash_categories'))
    
    sidebar_labels = Status.query.order_by('id')

    if request.method == 'POST':
        if form.cancel.data:
            return redirect(url_for('main.dash_categories'))
    if form.validate_on_submit():
        # if the entered name doesn't match the category name, prompt an error
        if form.name.data != category.name:
            flash('Entered name does not match!', 'form-error')
        # category name confirmed, delete category
        else:
            db.session.delete(category)
            db.session.commit()
            return redirect(url_for('main.dash_categories'))
    return render_template('dash/categories/delete_category.html', title='Dashboard - Delete Category', sidebar=sidebar_labels, form=form, category=category)

# 
# 
# 
# 
# Themes
# 
# 
# 
#
@bp.route('/dashboard/themes')
@login_required
@rank_required('SUPERADMIN', 'ADMIN', 'MODERATOR')
def dash_themes():
    filters = get_session_filters('themes')
    page = get_value(request.args.get('page', type=int), filters.get('page') if filters else None, 1)
    size = get_value(request.args.get('size', type=int), filters.get('size') if filters else None, 20)
    order = get_value(request.args.get('order', type=str), filters.get('order') if filters else None, 'asc')
    sort = get_value(request.args.get('sort', type=str), filters.get('sort') if filters else None, 'id')
    search = get_value(request.args.get('search', type=str), filters.get('search') if filters else None, '')
    set_session_filters('themes', page, size, order, sort, search)
    columns = {
        'id': 'ID',
        'name': 'Name',
        'clips': 'Clips',
        'notes': 'Notes',
        'created_by': 'Created By',
        'created_at': 'Created At',
        'updated_by': 'Updated By',
        'updated_at': 'Updated At'
    }
    # Make sure the sort input is valid
    if sort in columns.keys():
        # Sorting by clip count requires joining Clip and Theme tables
        if sort == 'clips':
            query = Theme.query.outerjoin(clip_themes, Theme.id == clip_themes.c.theme_id).outerjoin(Clip, Clip.id == clip_themes.c.clip_id).group_by(Theme.id).filter(
                or_(
                    Theme.id.ilike(f'%{search}%'),
                    Theme.name.ilike(f'%{search}%'),
                    Theme.notes.ilike(f'%{search}%'),
                    Theme.created_by.ilike(f'%{search}%'),
                    Theme.created_at.ilike(f'%{search}%'),
                    Theme.updated_at.ilike(f'%{search}%')
                )
            ).order_by(db.func.count(Clip.id).desc() if order == 'desc' else db.func.count(Clip.id).asc())
        else:
            query = Theme.query.filter(
                or_(
                    Theme.id.ilike(f'%{search}%'),
                    Theme.name.ilike(f'%{search}%'),
                    Theme.notes.ilike(f'%{search}%'),
                    Theme.created_by.ilike(f'%{search}%'),
                    Theme.created_at.ilike(f'%{search}%'),
                    Theme.updated_at.ilike(f'%{search}%')
                )
            ).order_by(getattr(Theme, sort).desc() if order == 'desc' else getattr(Theme, sort).asc())
    else:
        # Default to sort by id
        query = Theme.query.filter(
            or_(
                Theme.id.ilike(f'%{search}%'),
                Theme.name.ilike(f'%{search}%'),
                Theme.notes.ilike(f'%{search}%'),
                Theme.created_by.ilike(f'%{search}%'),
                Theme.created_at.ilike(f'%{search}%'),
                Theme.updated_at.ilike(f'%{search}%')
            )
        ).order_by(Theme.id.desc() if order == 'desc' else Theme.id.asc())
    # Default to page 1 if page number isn't valid
    if page > math.ceil(query.count()/size) or page < 1:
        page = 1
    themes = db.paginate(query, page=page, per_page=size, error_out=False)
    pages = themes.iter_pages(left_edge=2, left_current=1, right_edge=2, right_current=1)
    sidebar_labels = Status.query.order_by('id')
    return render_template('dash/themes/themes.html', title='Dashboard - Themes', sidebar=sidebar_labels, themes=themes, page=page, pages=pages, size=size, order=order, sort=sort, search=search, columns=columns)

@bp.route('/dashboard/themes/create', methods=['GET', 'POST'])
@login_required
@rank_required('SUPERADMIN', 'ADMIN', 'MODERATOR')
def dash_themes_create():
    form = themeForm()
    sidebar_labels = Status.query.order_by('id')
    if request.method == 'POST':
        if form.cancel.data:
            return redirect(url_for('main.dash_themes'))
    if form.validate_on_submit():
        theme = Theme.query.filter(Theme.name.ilike(form.name.data)).first()
        # theme doesn't already exist, create it
        if theme is None:
            theme = Theme(name=form.name.data,
                                notes=form.notes.data,
                                created_at=datetime.now(timezone.utc),
                                updated_at=datetime.now(timezone.utc),
                                created_by=current_user.twitch_id,
                                updated_by=current_user.twitch_id)
            db.session.add(theme)
            db.session.commit()
            return redirect(url_for('main.dash_themes'))
        # theme already exists, prompt name change
        else:
            flash('Name must be unique!', 'form-error')
    return render_template('dash/themes/create_theme.html', title='Dashboard - Create Theme', sidebar=sidebar_labels, form=form)
    
@bp.route('/dashboard/themes/<id>/edit', methods=['GET', 'POST'])
@login_required
@rank_required('SUPERADMIN', 'ADMIN', 'MODERATOR')
def dash_themes_edit(id):
    current_theme = Theme.query.filter(Theme.id == id).first()
    current_theme_info = []
    if current_theme != None:
        current_theme_info = [current_theme.name, current_theme.notes] # list to compare to for edits
        # populate the form with the existing data
        form = themeForm(name=current_theme.name, notes=current_theme.notes)
    else:
        return redirect(url_for('main.dash_themes'))
    
    sidebar_labels = Status.query.order_by('id')

    if request.method == 'POST':
        if form.cancel.data:
            return redirect(url_for('main.dash_themes'))
    if form.validate_on_submit():
        form_info = [form.name.data, form.notes.data] # list to compare with current_theme_info
        # if the form data hasn't changed, just redirect to themes page
        if form_info == current_theme_info:
            return redirect(url_for('main.dash_themes'))
        # otherwise handle changes
        else:
            theme = Theme.query.filter(Theme.name.ilike(form.name.data)).first()
            # theme doesn't already exist or is the current theme, allow edit
            if theme is None or theme.name == current_theme.name:
                current_theme.name = form.name.data
                current_theme.notes = form.notes.data
                current_theme.updated_at = datetime.now(timezone.utc)
                current_theme.updated_by = current_user.twitch_id
                db.session.commit()
                return redirect(url_for('main.dash_themes'))
            # theme already exists, prompt name change
            else:
                flash('Name must be unique!', 'form-error')
    return render_template('dash/themes/edit_theme.html', title='Dashboard - Edit Theme', sidebar=sidebar_labels, form=form)

@bp.route('/dashboard/themes/<id>/delete', methods=['GET', 'POST'])
@login_required
@rank_required('SUPERADMIN', 'ADMIN')
def dash_themes_delete(id):
    theme = Theme.query.filter(Theme.id == id).first()
    if theme != None:
        if len(theme.clips) > 0:
            # Don't allow deletion of themes with clips assigned
            return redirect(url_for('main.dash_themes'))
        form = deleteForm()
    else:
        return redirect(url_for('main.dash_themes'))
    
    sidebar_labels = Status.query.order_by('id')

    if request.method == 'POST':
        if form.cancel.data:
            return redirect(url_for('main.dash_themes'))
    if form.validate_on_submit():
        # if the entered name doesn't match the theme name, prompt an error
        if form.name.data != theme.name:
            flash('Entered name does not match!', 'form-error')
        # theme name confirmed, delete theme
        else:
            db.session.delete(theme)
            db.session.commit()
            return redirect(url_for('main.dash_themes'))
    return render_template('dash/themes/delete_theme.html', title='Dashboard - Delete Theme', sidebar=sidebar_labels, form=form, theme=theme)
    
# 
# 
# 
# 
# Subjects
# 
# 
# 
#
@bp.route('/dashboard/subjects')
@login_required
@rank_required('SUPERADMIN', 'ADMIN', 'MODERATOR')
def dash_subjects():
    filters = get_session_filters('subjects')
    page = get_value(request.args.get('page', type=int), filters.get('page') if filters else None, 1)
    size = get_value(request.args.get('size', type=int), filters.get('size') if filters else None, 20)
    order = get_value(request.args.get('order', type=str), filters.get('order') if filters else None, 'asc')
    sort = get_value(request.args.get('sort', type=str), filters.get('sort') if filters else None, 'id')
    search = get_value(request.args.get('search', type=str), filters.get('search') if filters else None, '')
    set_session_filters('subjects', page, size, order, sort, search)
    columns = {
        'id': 'ID',
        'name': 'Name',
        'category_id': 'Category',
        'clips': 'Clips',
        'subtext': 'Subtext',
        'keywords': 'Keywords',
        'notes': 'Notes',
        'public': 'Public',
        'created_by': 'Created By',
        'created_at': 'Created At',
        'updated_by': 'Updated By',
        'updated_at': 'Updated At'
    }
    # Make sure the sort input is valid
    if sort in columns.keys():
        # Sorting by clip count requires joining Clip and Subject tables
        if sort == 'clips':
            query = Subject.query.outerjoin(clip_subjects, Subject.id == clip_subjects.c.subject_id).outerjoin(Clip, Clip.id == clip_subjects.c.clip_id).group_by(Subject.id).filter(
                or_(
                    Subject.id.ilike(f'%{search}%'),
                    Subject.name.ilike(f'%{search}%'),
                    # TODO Subject.category_id.name.ilike(f'%{search}%'),
                    Subject.subtext.ilike(f'%{search}%'),
                    Subject.keywords.ilike(f'%{search}%'),
                    Subject.notes.ilike(f'%{search}%'),
                    Subject.created_by.ilike(f'%{search}%'),
                    Subject.created_at.ilike(f'%{search}%'),
                    Subject.updated_at.ilike(f'%{search}%')
                )
            ).order_by(db.func.count(Clip.id).desc() if order == 'desc' else db.func.count(Clip.id).asc())
        else:
            query = Subject.query.filter(
                or_(
                    Subject.id.ilike(f'%{search}%'),
                    Subject.name.ilike(f'%{search}%'),
                    # TODO Subject.category_id.name.ilike(f'%{search}%'),
                    Subject.subtext.ilike(f'%{search}%'),
                    Subject.keywords.ilike(f'%{search}%'),
                    Subject.notes.ilike(f'%{search}%'),
                    Subject.created_by.ilike(f'%{search}%'),
                    Subject.created_at.ilike(f'%{search}%'),
                    Subject.updated_at.ilike(f'%{search}%')
                )
            ).order_by(getattr(Subject, sort).desc() if order == 'desc' else getattr(Subject, sort).asc())
    else:
        # Default to sort by id
        query = Subject.query.filter(
            or_(
                Subject.id.ilike(f'%{search}%'),
                Subject.name.ilike(f'%{search}%'),
                # TODO Subject.category_id.name.ilike(f'%{search}%'),
                Subject.subtext.ilike(f'%{search}%'),
                Subject.keywords.ilike(f'%{search}%'),
                Subject.notes.ilike(f'%{search}%'),
                Subject.created_by.ilike(f'%{search}%'),
                Subject.created_at.ilike(f'%{search}%'),
                Subject.updated_at.ilike(f'%{search}%')
            )
        ).order_by(Subject.id.desc() if order == 'desc' else Subject.id.asc())
    # Default to page 1 if page number isn't valid
    if page > math.ceil(query.count()/size) or page < 1:
        page = 1
    subjects = db.paginate(query, page=page, per_page=size, error_out=False)
    pages = subjects.iter_pages(left_edge=2, left_current=1, right_edge=2, right_current=1)
    sidebar_labels = Status.query.order_by('id')
    return render_template('dash/subjects/subjects.html', title='Dashboard - Subjects', sidebar=sidebar_labels, subjects=subjects, page=page, pages=pages, size=size, order=order, sort=sort, search=search, columns=columns)
    
@bp.route('/dashboard/subjects/create', methods=['GET', 'POST'])
@login_required
@rank_required('SUPERADMIN', 'ADMIN', 'MODERATOR')
def dash_subjects_create():
    form = subjectForm()
    form.category.choices = [(c.id, c.name) for c in SubjectCategory.query.order_by('id')]
    sidebar_labels = Status.query.order_by('id')
    if request.method == 'POST':
        if form.cancel.data:
            return redirect(url_for('main.dash_subjects'))
    if form.validate_on_submit():
        subject = Subject.query.filter(Subject.name.ilike(form.name.data)).first()
        # subject doesn't already exist, create it
        if subject is None:
            subject = Subject(name=form.name.data,
                            category_id=form.category.data,
                            subtext=form.subtext.data,
                            public=form.public.data,
                            keywords=form.keywords.data,
                            notes=form.notes.data,
                            created_at=datetime.now(timezone.utc),
                            updated_at=datetime.now(timezone.utc),
                            created_by=current_user.twitch_id,
                            updated_by=current_user.twitch_id)
            db.session.add(subject)
            db.session.commit()
            return redirect(url_for('main.dash_subjects'))
        # subject already exists, prompt name change
        else:
            flash('Name must be unique!', 'form-error')
    return render_template('dash/subjects/create_subject.html', title='Dashboard - Create Subject', sidebar=sidebar_labels, form=form)
    
@bp.route('/dashboard/subjects/<id>/edit', methods=['GET', 'POST'])
@login_required
@rank_required('SUPERADMIN', 'ADMIN', 'MODERATOR')
def dash_subjects_edit(id):
    current_subject = Subject.query.filter(Subject.id == id).first()
    current_subject_info = []
    if current_subject != None:
        current_subject_info = [current_subject.name, current_subject.category_id, current_subject.subtext, current_subject.keywords, current_subject.public, current_subject.notes] # list to compare to for edits
        # populate the form with the existing data
        form = subjectForm(name=current_subject.name,
                            category=current_subject.category_id,
                            subtext=current_subject.subtext,
                            keywords=current_subject.keywords,
                            public=current_subject.public,
                            notes=current_subject.notes)
        form.category.choices = [(c.id, c.name) for c in SubjectCategory.query.order_by('id')]
    else:
        return redirect(url_for('main.dash_subjects'))
    
    sidebar_labels = Status.query.order_by('id')

    if request.method == 'POST':
        if form.cancel.data:
            return redirect(url_for('main.dash_subjects'))
    if form.validate_on_submit():
        form_info = [form.name.data, form.category.data, form.subtext.data, form.keywords.data, form.public.data, form.notes.data] # list to compare with current_subject_info
        # if the form data hasn't changed, just redirect to subjects page
        if form_info == current_subject_info:
            return redirect(url_for('main.dash_subjects'))
        # otherwise handle changes
        else:
            subject = Subject.query.filter(Subject.name.ilike(form.name.data)).first()
            # subject doesn't already exist or is the current subject, allow edit
            if subject is None or subject.name == current_subject.name:
                current_subject.name = form.name.data
                current_subject.category_id = form.category.data
                current_subject.subtext = form.subtext.data
                current_subject.keywords = form.keywords.data
                current_subject.public = form.public.data
                current_subject.notes = form.notes.data
                current_subject.updated_at = datetime.now(timezone.utc)
                current_subject.updated_by = current_user.twitch_id
                db.session.commit()
                return redirect(url_for('main.dash_subjects'))
            # subject already exists, prompt name change
            else:
                flash('Name must be unique!', 'form-error')
    return render_template('dash/subjects/edit_subject.html', title='Dashboard - Edit Subject', sidebar=sidebar_labels, form=form)

@bp.route('/dashboard/subjects/<id>/delete', methods=['GET', 'POST'])
@login_required
@rank_required('SUPERADMIN', 'ADMIN')
def dash_subjects_delete(id):
    subject = Subject.query.filter(Subject.id == id).first()
    if subject != None:
        if len(subject.clips) > 0:
            # Don't allow deletion of subjects with clips assigned
            return redirect(url_for('main.dash_subjects'))
        form = deleteForm()
    else:
        return redirect(url_for('main.dash_subjects'))
    
    sidebar_labels = Status.query.order_by('id')

    if request.method == 'POST':
        if form.cancel.data:
            return redirect(url_for('main.dash_subjects'))
    if form.validate_on_submit():
        # if the entered name doesn't match the subject name, prompt an error
        if form.name.data != subject.name:
            flash('Entered name does not match!', 'form-error')
        # subject name confirmed, delete subject
        else:
            db.session.delete(subject)
            db.session.commit()
            return redirect(url_for('main.dash_subjects'))
    return render_template('dash/subjects/delete_subject.html', title='Dashboard - Delete Subject', sidebar=sidebar_labels, form=form, subject=subject)    

# 
# 
# 
# 
# Subject Categories
# 
# 
# 
#
@bp.route('/dashboard/subject_categories')
@login_required
@rank_required('SUPERADMIN', 'ADMIN', 'MODERATOR')
def dash_subject_categories():
    filters = get_session_filters('subject_categories')
    page = get_value(request.args.get('page', type=int), filters.get('page') if filters else None, 1)
    size = get_value(request.args.get('size', type=int), filters.get('size') if filters else None, 20)
    order = get_value(request.args.get('order', type=str), filters.get('order') if filters else None, 'asc')
    sort = get_value(request.args.get('sort', type=str), filters.get('sort') if filters else None, 'id')
    search = get_value(request.args.get('search', type=str), filters.get('search') if filters else None, '')
    set_session_filters('subject_categories', page, size, order, sort, search)
    columns = {
        'id': 'ID',
        'name': 'Name',
        'subjects': 'Subjects',
        'notes': 'Notes',
        'created_by': 'Created By',
        'created_at': 'Created At',
        'updated_by': 'Updated By',
        'updated_at': 'Updated At'
    }
    # Make sure the sort input is valid
    if sort in columns.keys():
        # Sorting by subject count requires joining Subject and SubjectCategory tables
        if sort == 'clips':
            query = SubjectCategory.query.outerjoin(Subject, SubjectCategory.id == Subject.category_id).group_by(SubjectCategory.id).filter(
                or_(
                    SubjectCategory.id.ilike(f'%{search}%'),
                    SubjectCategory.name.ilike(f'%{search}%'),
                    SubjectCategory.notes.ilike(f'%{search}%'),
                    SubjectCategory.created_by.ilike(f'%{search}%'),
                    SubjectCategory.created_at.ilike(f'%{search}%'),
                    SubjectCategory.updated_at.ilike(f'%{search}%')
                )
            ).order_by(db.func.count(Subject.id).desc() if order == 'desc' else db.func.count(Subject.id).asc())
        else:
            query = SubjectCategory.query.filter(
                or_(
                    SubjectCategory.id.ilike(f'%{search}%'),
                    SubjectCategory.name.ilike(f'%{search}%'),
                    SubjectCategory.notes.ilike(f'%{search}%'),
                    SubjectCategory.created_by.ilike(f'%{search}%'),
                    SubjectCategory.created_at.ilike(f'%{search}%'),
                    SubjectCategory.updated_at.ilike(f'%{search}%')
                )
            ).order_by(getattr(SubjectCategory, sort).desc() if order == 'desc' else getattr(SubjectCategory, sort).asc())
    else:
        # Default to sort by id
        query = SubjectCategory.query.filter(
            or_(
                SubjectCategory.id.ilike(f'%{search}%'),
                SubjectCategory.name.ilike(f'%{search}%'),
                SubjectCategory.notes.ilike(f'%{search}%'),
                SubjectCategory.created_by.ilike(f'%{search}%'),
                SubjectCategory.created_at.ilike(f'%{search}%'),
                SubjectCategory.updated_at.ilike(f'%{search}%')
            )
        ).order_by(SubjectCategory.id.desc() if order == 'desc' else SubjectCategory.id.asc())
    # Default to page 1 if page number isn't valid
    if page > math.ceil(query.count()/size) or page < 1:
        page = 1
    subject_categories = db.paginate(query, page=page, per_page=size, error_out=False)
    pages = subject_categories.iter_pages(left_edge=2, left_current=1, right_edge=2, right_current=1)
    sidebar_labels = Status.query.order_by('id')
    return render_template('dash/subject_categories/subject_categories.html', title='Dashboard - Subject Categories', sidebar=sidebar_labels, subject_categories=subject_categories, page=page, pages=pages, size=size, order=order, sort=sort, search=search, columns=columns)
   
@bp.route('/dashboard/subject_categories/create', methods=['GET', 'POST'])
@login_required
@rank_required('SUPERADMIN', 'ADMIN', 'MODERATOR')
def dash_subject_categories_create():
    form = subjectCategoryForm()
    sidebar_labels = Status.query.order_by('id')
    if request.method == 'POST':
        if form.cancel.data:
            return redirect(url_for('main.dash_subject_categories'))
    if form.validate_on_submit():
        subject_category = SubjectCategory.query.filter(SubjectCategory.name.ilike(form.name.data)).first()
        # subject category doesn't already exist, create it
        if subject_category is None:
            subject_category = SubjectCategory(name=form.name.data,
                                                notes=form.notes.data,
                                                created_at=datetime.now(timezone.utc),
                                                updated_at=datetime.now(timezone.utc),
                                                created_by=current_user.twitch_id,
                                                updated_by=current_user.twitch_id)
            db.session.add(subject_category)
            db.session.commit()
            return redirect(url_for('main.dash_subject_categories'))
        # subject category already exists, prompt name change
        else:
            flash('Name must be unique!', 'form-error')
    return render_template('dash/subject_categories/create_subject_category.html', title='Dashboard - Create Subject Category', sidebar=sidebar_labels, form=form)
    
@bp.route('/dashboard/subject_categories/<id>/edit', methods=['GET', 'POST'])
@login_required
@rank_required('SUPERADMIN', 'ADMIN', 'MODERATOR')
def dash_subject_categories_edit(id):
    current_subject_category = SubjectCategory.query.filter(SubjectCategory.id == id).first()
    current_subject_category_info = []
    if current_subject_category != None:
        current_subject_category_info = [current_subject_category.name, current_subject_category.notes] # list to compare to for edits
        # populate the form with the existing data
        form = subjectCategoryForm(name=current_subject_category.name,
                                    notes=current_subject_category.notes)
    else:
        return redirect(url_for('main.dash_subject_categories'))
    
    sidebar_labels = Status.query.order_by('id')

    if request.method == 'POST':
        if form.cancel.data:
            return redirect(url_for('main.dash_subject_categories'))
    if form.validate_on_submit():
        form_info = [form.name.data, form.notes.data] # list to compare with current_subject_category_info
        # if the form data hasn't changed, just redirect to subject categories page
        if form_info == current_subject_category_info:
            return redirect(url_for('main.dash_subject_categories'))
        # otherwise handle changes
        else:
            subject_category = SubjectCategory.query.filter(SubjectCategory.name.ilike(form.name.data)).first()
            # subject category doesn't already exist or is the current subject category, allow edit
            if subject_category is None or subject_category.name == current_subject_category.name:
                current_subject_category.name = form.name.data
                current_subject_category.notes = form.notes.data
                current_subject_category.updated_at = datetime.now(timezone.utc)
                current_subject_category.updated_by = current_user.twitch_id
                db.session.commit()
                return redirect(url_for('main.dash_subject_categories'))
            # subject category already exists, prompt name change
            else:
                flash('Name must be unique!', 'form-error')
    return render_template('dash/subject_categories/edit_subject_category.html', title='Dashboard - Edit Subject Category', sidebar=sidebar_labels, form=form)

@bp.route('/dashboard/subject_categories/<id>/delete', methods=['GET', 'POST'])
@login_required
@rank_required('SUPERADMIN', 'ADMIN')
def dash_subject_categories_delete(id):
    subject_category = SubjectCategory.query.filter(SubjectCategory.id == id).first()
    if subject_category != None:
        if len(subject_category.subjects) > 0:
            # Don't allow deletion of subject categories with subjects assigned
            return redirect(url_for('main.dash_subject_categories'))
        form = deleteForm()
    else:
        return redirect(url_for('main.dash_subject_categories'))
    
    sidebar_labels = Status.query.order_by('id')

    if request.method == 'POST':
        if form.cancel.data:
            return redirect(url_for('main.dash_subject_categories'))
    if form.validate_on_submit():
        # if the entered name doesn't match the subject_category name, prompt an error
        if form.name.data != subject_category.name:
            flash('Entered name does not match!', 'form-error')
        # subject_category name confirmed, delete subject_category
        else:
            db.session.delete(subject_category)
            db.session.commit()
            return redirect(url_for('main.dash_subject_categories'))
    return render_template('dash/subject_categories/delete_subject_category.html', title='Dashboard - Delete Subject Category', sidebar=sidebar_labels, form=form, subject_category=subject_category)    


# 
# 
# 
# 
# Status Labels
# 
# 
# 
#
@bp.route('/dashboard/statuslabels')
@login_required
@rank_required('SUPERADMIN', 'ADMIN', 'MODERATOR')
def dash_statuslabels():
    filters = get_session_filters('statuslabels')
    page = get_value(request.args.get('page', type=int), filters.get('page') if filters else None, 1)
    size = get_value(request.args.get('size', type=int), filters.get('size') if filters else None, 20)
    order = get_value(request.args.get('order', type=str), filters.get('order') if filters else None, 'asc')
    sort = get_value(request.args.get('sort', type=str), filters.get('sort') if filters else None, 'id')
    search = get_value(request.args.get('search', type=str), filters.get('search') if filters else None, '')
    set_session_filters('statuslabels', page, size, order, sort, search)
    columns = {
        'id': 'ID',
        'name': 'Name',
        'type': 'Status Type',
        'clips': 'Clips',
        'color': 'Color',
        'notes': 'Notes',
        'created_by': 'Created By',
        'created_at': 'Created At',
        'updated_by': 'Updated By',
        'updated_at': 'Updated At'
    }
    # Make sure the sort input is valid
    if sort in columns.keys():
        # Sorting by clip count requires joining Clip and Status tables
        if sort == 'clips':
            query = Status.query.outerjoin(Clip, Status.id == Clip.status_id).group_by(Status.id).filter(
                or_(
                    Status.id.ilike(f'%{search}%'),
                    Status.name.ilike(f'%{search}%'),
                    Status.type.ilike(f'%{search}%'),
                    Status.color.ilike(f'%{search}%'),
                    Status.notes.ilike(f'%{search}%'),
                    Status.created_by.ilike(f'%{search}%'),
                    Status.created_at.ilike(f'%{search}%'),
                    Status.updated_at.ilike(f'%{search}%')
                )
            ).order_by(db.func.count(Clip.id).desc() if order == 'desc' else db.func.count(Clip.id).asc())
        else:
            query = Status.query.filter(
                or_(
                    Status.id.ilike(f'%{search}%'),
                    Status.name.ilike(f'%{search}%'),
                    Status.type.ilike(f'%{search}%'),
                    Status.color.ilike(f'%{search}%'),
                    Status.notes.ilike(f'%{search}%'),
                    Status.created_by.ilike(f'%{search}%'),
                    Status.created_at.ilike(f'%{search}%'),
                    Status.updated_at.ilike(f'%{search}%')
                )
            ).order_by(getattr(Status, sort).desc() if order == 'desc' else getattr(Status, sort).asc())
    else:
        # Default to sort by id
        query = Status.query.filter(
            or_(
                Status.id.ilike(f'%{search}%'),
                Status.name.ilike(f'%{search}%'),
                Status.type.ilike(f'%{search}%'),
                Status.color.ilike(f'%{search}%'),
                Status.notes.ilike(f'%{search}%'),
                Status.created_by.ilike(f'%{search}%'),
                Status.created_at.ilike(f'%{search}%'),
                Status.updated_at.ilike(f'%{search}%')
            )
        ).order_by(Status.id.desc() if order == 'desc' else Status.id.asc())
    # Default to page 1 if page number isn't valid
    if page > math.ceil(query.count()/size) or page < 1:
        page = 1
    status_labels = db.paginate(query, page=page, per_page=size, error_out=False)
    pages = status_labels.iter_pages(left_edge=2, left_current=1, right_edge=2, right_current=1)
    sidebar_labels = Status.query.order_by('id')
    return render_template('dash/statuslabels/statuslabels.html', title='Dashboard - Status Labels', sidebar=sidebar_labels, status_labels=status_labels, page=page, pages=pages, size=size, order=order, sort=sort, search=search, columns=columns)
    
@bp.route('/dashboard/statuslabels/create', methods=['GET', 'POST'])
@login_required
@rank_required('SUPERADMIN', 'ADMIN', 'MODERATOR')
def dash_statuslabels_create():
    form = statusLabelForm()
    sidebar_labels = Status.query.order_by('id')
    if request.method == 'POST':
        if form.cancel.data:
            return redirect(url_for('main.dash_statuslabels'))
    if form.validate_on_submit():
        status = Status.query.filter(Status.name.ilike(form.name.data)).first()
        # status doesn't already exist, create it
        if status is None:
            status = Status(name=form.name.data,
                            type=form.status_type.data,
                            color=form.color.data,
                            notes=form.notes.data,
                            created_at=datetime.now(timezone.utc),
                            updated_at=datetime.now(timezone.utc),
                            created_by=current_user.twitch_id,
                            updated_by=current_user.twitch_id)
            db.session.add(status)
            db.session.commit()
            return redirect(url_for('main.dash_statuslabels'))
        # status already exists, prompt name change
        else:
            flash('Name must be unique!', 'form-error')
    return render_template('dash/statuslabels/create_statuslabel.html', title='Dashboard - Create Status Label', sidebar=sidebar_labels, form=form)
    
@bp.route('/dashboard/statuslabels/<id>', methods=['GET', 'POST'])
@login_required
@rank_required('SUPERADMIN', 'ADMIN', 'MODERATOR')
def dash_statuslabels_clips(id):
    filters = get_session_filters('clips')
    page = get_value(request.args.get('page', type=int), filters.get('page') if filters else None, 1)
    size = get_value(request.args.get('size', type=int), filters.get('size') if filters else None, 20)
    order = get_value(request.args.get('order', type=str), filters.get('order') if filters else None, 'asc')
    sort = get_value(request.args.get('sort', type=str), filters.get('sort') if filters else None, 'id')
    search = get_value(request.args.get('search', type=str), filters.get('search') if filters else None, '')
    set_session_filters('clips', page, size, order, sort, search)
    columns = {
        'id': 'ID',
        'twitch_id': 'Twitch ID',
        'broadcaster_name': 'Broadcaster',
        'creator_name': 'Creator',
        'title': 'Title',
        'title_override': 'Title Override',
        'view_count': 'Views',
        'created_at': 'Created At',
        'updated_by': 'Updated By',
        'updated_at': 'Updated At',
        'duration': 'Duration',
        'notes': 'Notes',
        'category': 'Category',
        'status': 'Status',
        'themes': 'Themes',
        'subjects': 'Subjects',
    }
    statuslabel = Status.query.filter(Status.id == id).first()
    # Make sure the sort input is valid
    if sort in columns.keys():
        if sort == 'clips':
            query = Clip.query.outerjoin(Clip, Clip.twitch_id == Clip.creator_id).group_by(Clip.twitch_id).filter(
                or_(
                    Clip.twitch_id.ilike(f'%{search}%'),
                    Clip.broadcaster_name.ilike(f'%{search}%'),
                    Clip.creator_name.ilike(f'%{search}%'),
                    Clip.title.ilike(f'%{search}%'),
                    Clip.title_override.ilike(f'%{search}%'),
                    Clip.notes.ilike(f'%{search}%'),
                    # Clip.category.ilike(f'%{search}%'),
                    # Clip.themes.ilike(f'%{search}%'),
                    # Clip.subjects.ilike(f'%{search}%')
                ),
                Clip.status_id == id
            ).order_by(db.func.count(Clip.id).desc() if order == 'desc' else db.func.count(Clip.id).asc())
        elif sort == 'rank':
            query = Clip.query.outerjoin(Rank, Clip.rank_id == Rank.id).filter(
                or_(
                    Clip.twitch_id.ilike(f'%{search}%'),
                    Clip.broadcaster_name.ilike(f'%{search}%'),
                    Clip.creator_name.ilike(f'%{search}%'),
                    Clip.title.ilike(f'%{search}%'),
                    Clip.title_override.ilike(f'%{search}%'),
                    Clip.notes.ilike(f'%{search}%'),
                    # Clip.category.ilike(f'%{search}%'),
                    # Clip.themes.ilike(f'%{search}%'),
                    # Clip.subjects.ilike(f'%{search}%')
                ),
                Clip.status_id == id
            ).order_by(Rank.id.desc() if order == 'desc' else Rank.id.asc())
        else:
            query = Clip.query.filter(
                or_(
                    Clip.twitch_id.ilike(f'%{search}%'),
                    Clip.broadcaster_name.ilike(f'%{search}%'),
                    Clip.creator_name.ilike(f'%{search}%'),
                    Clip.title.ilike(f'%{search}%'),
                    Clip.title_override.ilike(f'%{search}%'),
                    Clip.notes.ilike(f'%{search}%'),
                    # Clip.category.ilike(f'%{search}%'),
                    # Clip.themes.ilike(f'%{search}%'),
                    # Clip.subjects.ilike(f'%{search}%')
                ),
                Clip.status_id == id
            ).order_by(getattr(Clip, sort).desc() if order == 'desc' else getattr(Clip, sort).asc())
    else:
        # Default to sort by id
        query = Clip.query.filter(
            or_(
                Clip.twitch_id.ilike(f'%{search}%'),
                Clip.broadcaster_name.ilike(f'%{search}%'),
                Clip.creator_name.ilike(f'%{search}%'),
                Clip.title.ilike(f'%{search}%'),
                Clip.title_override.ilike(f'%{search}%'),
                Clip.notes.ilike(f'%{search}%'),
                # Clip.category.ilike(f'%{search}%'),
                # Clip.themes.ilike(f'%{search}%'),
                # Clip.subjects.ilike(f'%{search}%')
            ),
            Clip.status_id == id
        ).order_by(Clip.id.desc() if order == 'desc' else Clip.id.asc())
    # Default to page 1 if page number isn't valid
    if page > math.ceil(query.count()/size) or page < 1:
        page = 1
    clips = db.paginate(query, page=page, per_page=size, error_out=False)
    pages = clips.iter_pages(left_edge=2, left_current=1, right_edge=2, right_current=1)
    sidebar_labels = Status.query.order_by('id')
    return render_template('dash/statuslabels/statuslabel_clips.html', title=f'Dashboard - {statuslabel.name}', header=statuslabel.name, sidebar=sidebar_labels, clips=clips, page=page, pages=pages, size=size, order=order, sort=sort, search=search, columns=columns)

@bp.route('/dashboard/statuslabels/<id>/edit', methods=['GET', 'POST'])
@login_required
@rank_required('SUPERADMIN', 'ADMIN', 'MODERATOR')
def dash_statuslabels_edit(id):
    current_status = Status.query.filter(Status.id == id).first()
    current_status_info = []
    if current_status != None:
        current_status_info = [current_status.name, current_status.type, current_status.color, current_status.notes] # list to compare to for edits
        # populate the form with the existing data
        form = statusLabelForm(name=current_status.name,
                                status_type=current_status.type,
                                color=current_status.color,
                                notes=current_status.notes)
    else:
        return redirect(url_for('main.dash_statuslabels'))
    
    sidebar_labels = Status.query.order_by('id')

    if request.method == 'POST':
        if form.cancel.data:
            return redirect(url_for('main.dash_statuslabels'))
    if form.validate_on_submit():
        form_info = [form.name.data, form.status_type.data, form.color.data, form.notes.data] # list to compare with current_status_info
        # if the form data hasn't changed, just redirect to statuslabels page
        if form_info == current_status_info:
            return redirect(url_for('main.dash_statuslabels'))
        # otherwise handle changes
        else:
            status = Status.query.filter(Status.name.ilike(form.name.data)).first()
            # status doesn't already exist or is the current status, allow edit
            if status is None or status.name == current_status.name:
                current_status.name = form.name.data
                current_status.type = form.status_type.data
                current_status.color = form.color.data
                current_status.notes = form.notes.data
                current_status.updated_at = datetime.now(timezone.utc)
                current_status.updated_by = current_user.twitch_id
                db.session.commit()
                return redirect(url_for('main.dash_statuslabels'))
            # status already exists, prompt name change
            else:
                flash('Name must be unique!', 'form-error')
    return render_template('dash/statuslabels/edit_statuslabel.html', title='Dashboard - Edit Status Label', sidebar=sidebar_labels, form=form)

@bp.route('/dashboard/statuslabels/<id>/delete', methods=['GET', 'POST'])
@login_required
@rank_required('SUPERADMIN', 'ADMIN')
def dash_statuslabels_delete(id):
    status = Status.query.filter(Status.id == id).first()
    if status != None:
        if len(status.clips) > 0:
            # Don't allow deletion of statuses with clips assigned
            return redirect(url_for('main.dash_statuslabels'))
        if status.id == 1:
            # Don't allow deletion of ID 1 since it is the default
            return redirect(url_for('main.dash_statuslabels'))
        form = deleteForm()
    else:
        return redirect(url_for('main.dash_statuslabels'))
    
    sidebar_labels = Status.query.order_by('id')

    if request.method == 'POST':
        if form.cancel.data:
            return redirect(url_for('main.dash_statuslabels'))
    if form.validate_on_submit():
        # if the entered name doesn't match the status name, prompt an error
        if form.name.data != status.name:
            flash('Entered name does not match!', 'form-error')
        # status name confirmed, delete status
        else:
            db.session.delete(status)
            db.session.commit()
            return redirect(url_for('main.dash_statuslabels'))
    return render_template('dash/statuslabels/delete_statuslabel.html', title='Dashboard - Delete Status Label', sidebar=sidebar_labels, form=form, status=status)