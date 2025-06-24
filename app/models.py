from datetime import datetime, timezone
import sqlalchemy as sa
import sqlalchemy.orm as so
from flask_login import UserMixin
from typing import List
from app import db, login

# Define the association table between User and Clip for upvotes
upvotes = sa.Table(
    'upvotes',
    db.metadata,
    sa.Column('user_id', sa.String(32), sa.ForeignKey('user.id'), primary_key=True),
    sa.Column('clip_id', sa.String(64), sa.ForeignKey('clip.id'), primary_key=True)
)

# Define the association table between Clip and Theme
clip_themes = sa.Table(
    'clip_themes',
    db.metadata,
    sa.Column('clip_id', sa.String(64), sa.ForeignKey('clip.id'), primary_key=True),
    sa.Column('theme_id', sa.Integer, sa.ForeignKey('theme.id'), primary_key=True)
)

# Define the association table between Clip and Subject
clip_subjects = sa.Table(
    'clip_subjects',
    db.metadata,
    sa.Column('clip_id', sa.String(64), sa.ForeignKey('clip.id'), primary_key=True),
    sa.Column('subject_id', sa.Integer, sa.ForeignKey('subject.id'), primary_key=True)
)

class Rank(UserMixin, db.Model):
    id: so.Mapped[int] = so.mapped_column(sa.Integer, primary_key=True)
    name: so.Mapped[str] = so.mapped_column(sa.String(16), index=True, nullable=False, unique=True)

    users: so.Mapped[List['User']] = so.relationship(back_populates='rank')

    def __repr__(self):
        return f"<Rank id={self.id} name='{self.name}'>"

class User(UserMixin, db.Model):
    id: so.Mapped[int] = so.mapped_column(sa.Integer, primary_key=True)
    twitch_id: so.Mapped[int] = so.mapped_column(sa.Integer, index=True, unique=True)
    login: so.Mapped[str] = so.mapped_column(sa.String(32), index=True, unique=True)
    display_name: so.Mapped[str] = so.mapped_column(sa.String(32), index=True, unique=True)
    profile_image_url: so.Mapped[str] = so.mapped_column(sa.String(256))
    contributions: so.Mapped[int] = so.mapped_column(sa.Integer, default=0, nullable=False)
    last_verified: so.Mapped[datetime] = so.mapped_column(sa.DateTime, default=datetime.now(timezone.utc))
    access_token: so.Mapped[str] = so.mapped_column(sa.String(64), nullable=True)
    refresh_token: so.Mapped[str] = so.mapped_column(sa.String(64), nullable=True)
    notes: so.Mapped[str] = so.mapped_column(sa.Text, nullable=True)
    login_enabled: so.Mapped[bool] = so.mapped_column(sa.Boolean, server_default=sa.true(), nullable=False)
    updated_at: so.Mapped[datetime] = so.mapped_column(sa.DateTime, default=datetime.now(timezone.utc), nullable=True)

    rank_id: so.Mapped[int] = so.mapped_column(sa.ForeignKey(Rank.id), index=True, default=1)
    rank: so.Mapped[Rank] = so.relationship(back_populates='users')

    # Relationship to track clips a user has upvoted
    upvoted_clips: so.Mapped[List['Clip']] = so.relationship('Clip', secondary=upvotes, back_populates='upvoted_by')

    # Relationship to track activities performed by the user (admin)
    activities: so.Mapped[List['ActivityLog']] = so.relationship(back_populates='admin')

    updated_by: so.Mapped[int] = so.mapped_column(sa.Integer, sa.ForeignKey('user.twitch_id'), nullable=True)
    # Relationship to track the user who updated this user and users updated by this user
    updated_by_user: so.Mapped['User'] = so.relationship(
        'User',
        remote_side='User.twitch_id',
        back_populates='updated_users'
    )
    updated_users: so.Mapped[List['User']] = so.relationship(
        'User',
        back_populates='updated_by_user'
    )

    # Relationships to track categories created/updated by the user
    categories: so.Mapped[List['Category']] = so.relationship(
        'Category', back_populates='created_by_user', foreign_keys='Category.created_by'
    )
    updated_categories: so.Mapped[List['Category']] = so.relationship(
        'Category', back_populates='updated_by_user', foreign_keys='Category.updated_by'
    )

    # Relationships to track themes created/updated by the user
    themes: so.Mapped[List['Theme']] = so.relationship(
        'Theme', back_populates='created_by_user', foreign_keys='Theme.created_by'
    )
    updated_themes: so.Mapped[List['Theme']] = so.relationship(
        'Theme', back_populates='updated_by_user', foreign_keys='Theme.updated_by'
    )

    # Relationships to track statuses created/updated by the user
    statuses: so.Mapped[List['Status']] = so.relationship(
        'Status', back_populates='created_by_user', foreign_keys='Status.created_by'
    )
    updated_statuses: so.Mapped[List['Status']] = so.relationship(
        'Status', back_populates='updated_by_user', foreign_keys='Status.updated_by'
    )

    # Relationships to track subjects created/updated by the user
    subjects: so.Mapped[List['Subject']] = so.relationship(
        'Subject', back_populates='created_by_user', foreign_keys='Subject.created_by'
    )
    updated_subjects: so.Mapped[List['Subject']] = so.relationship(
        'Subject', back_populates='updated_by_user', foreign_keys='Subject.updated_by'
    )

    # Relationships to track subject categories created/updated by the user
    subject_categories: so.Mapped[List['Subject']] = so.relationship(
        'SubjectCategory', back_populates='created_by_user', foreign_keys='SubjectCategory.created_by'
    )
    updated_subject_categories: so.Mapped[List['Subject']] = so.relationship(
        'SubjectCategory', back_populates='updated_by_user', foreign_keys='SubjectCategory.updated_by'
    )

    # Relationships to track clips created/updated by the user
    created_clips: so.Mapped[List['Clip']] = so.relationship(
        'Clip',
        primaryjoin="User.twitch_id == Clip.creator_id",
        back_populates='creator',
        foreign_keys='Clip.creator_id'
    )
    updated_clips: so.Mapped[List['Clip']] = so.relationship(
        'Clip',
        back_populates='updated_by_user',
        foreign_keys='Clip.updated_by'
    )

    def __repr__(self):
        return f"<User id='{self.id}' login='{self.login}' display_name='{self.display_name}' rank='{self.rank}' contributions={self.contributions}>"

@login.user_loader
def load_user(id):
    return db.session.get(User, int(id))

class Category(db.Model):
    id: so.Mapped[int] = so.mapped_column(sa.Integer, primary_key=True)
    name: so.Mapped[str] = so.mapped_column(sa.String(32), unique=True, nullable=False)
    notes: so.Mapped[str] = so.mapped_column(sa.Text, nullable=True)
    created_at: so.Mapped[datetime] = so.mapped_column(sa.DateTime, default=datetime.now(timezone.utc), nullable=True)
    updated_at: so.Mapped[datetime] = so.mapped_column(sa.DateTime, default=datetime.now(timezone.utc), nullable=True)

    # Relationship to track which user created a category
    created_by: so.Mapped[int] = so.mapped_column(sa.Integer, sa.ForeignKey('user.twitch_id'), nullable=True)
    created_by_user: so.Mapped['User'] = so.relationship('User', back_populates='categories', foreign_keys=[created_by])

    # Relationship to track which user last updated a category
    updated_by: so.Mapped[int] = so.mapped_column(sa.Integer, sa.ForeignKey('user.twitch_id'), nullable=True)
    updated_by_user: so.Mapped['User'] = so.relationship('User', back_populates='updated_categories', foreign_keys=[updated_by])

    clips: so.Mapped[List['Clip']] = so.relationship(back_populates='category')
    
    def __repr__(self):
        return f'<Category {self.name}>'
    
class Theme(db.Model):
    id: so.Mapped[int] = so.mapped_column(sa.Integer, primary_key=True)
    name: so.Mapped[str] = so.mapped_column(sa.String(32), unique=True, nullable=False)
    notes: so.Mapped[str] = so.mapped_column(sa.Text, nullable=True)
    created_at: so.Mapped[datetime] = so.mapped_column(sa.DateTime, default=datetime.now(timezone.utc), nullable=True)
    updated_at: so.Mapped[datetime] = so.mapped_column(sa.DateTime, default=datetime.now(timezone.utc), nullable=True)

    # Relationship to track which user created a theme
    created_by: so.Mapped[int] = so.mapped_column(sa.Integer, sa.ForeignKey('user.twitch_id'), nullable=True)
    created_by_user: so.Mapped['User'] = so.relationship('User', back_populates='themes', foreign_keys=[created_by])

    # Relationship to track which user last updated a theme
    updated_by: so.Mapped[int] = so.mapped_column(sa.Integer, sa.ForeignKey('user.twitch_id'), nullable=True)
    updated_by_user: so.Mapped['User'] = so.relationship('User', back_populates='updated_themes', foreign_keys=[updated_by])

    # Relationship to track clips associated with a theme
    clips: so.Mapped[List['Clip']] = so.relationship('Clip', secondary=clip_themes, back_populates='themes')

    def __repr__(self):
        return f'<Theme {self.name}>'
    
class Status(db.Model):
    id: so.Mapped[int] = so.mapped_column(sa.Integer, primary_key=True)
    name: so.Mapped[str] = so.mapped_column(sa.String(32), unique=True, nullable=False)
    type = sa.Column(sa.Enum('Visible', 'Pending', 'Hidden', name='status_types'), nullable=False)
    color: so.Mapped[str] = so.mapped_column(sa.String(7), nullable=False)
    notes: so.Mapped[str] = so.mapped_column(sa.Text, nullable=True)
    created_at: so.Mapped[datetime] = so.mapped_column(sa.DateTime, default=datetime.now(timezone.utc), nullable=True)
    updated_at: so.Mapped[datetime] = so.mapped_column(sa.DateTime, default=datetime.now(timezone.utc), nullable=True)

    # Relationship to track which user created a status
    created_by: so.Mapped[int] = so.mapped_column(sa.Integer, sa.ForeignKey('user.twitch_id'), nullable=True)
    created_by_user: so.Mapped['User'] = so.relationship('User', back_populates='statuses', foreign_keys=[created_by])

    # Relationship to track which user last updated a status
    updated_by: so.Mapped[int] = so.mapped_column(sa.Integer, sa.ForeignKey('user.twitch_id'), nullable=True)
    updated_by_user: so.Mapped['User'] = so.relationship('User', back_populates='updated_statuses', foreign_keys=[updated_by])

    # Relationship to track clips associated with a status
    clips: so.Mapped[List['Clip']] = so.relationship(back_populates='status')

    def __repr__(self):
        return f'<Status {self.name}>'

class SubjectCategory(db.Model):
    id: so.Mapped[int] = so.mapped_column(sa.Integer, primary_key=True)
    name: so.Mapped[str] = so.mapped_column(sa.String(32), unique=True, nullable=False)
    notes: so.Mapped[str] = so.mapped_column(sa.Text, nullable=True)
    created_at: so.Mapped[datetime] = so.mapped_column(sa.DateTime, default=datetime.now(timezone.utc), nullable=True)
    updated_at: so.Mapped[datetime] = so.mapped_column(sa.DateTime, default=datetime.now(timezone.utc), nullable=True)

    # Relationship to track which user created a subject category
    created_by: so.Mapped[int] = so.mapped_column(sa.Integer, sa.ForeignKey('user.twitch_id'), nullable=True)
    created_by_user: so.Mapped['User'] = so.relationship('User', back_populates='subject_categories', foreign_keys=[created_by])

    # Relationship to track which user last updated a subject category
    updated_by: so.Mapped[int] = so.mapped_column(sa.Integer, sa.ForeignKey('user.twitch_id'), nullable=True)
    updated_by_user: so.Mapped['User'] = so.relationship('User', back_populates='updated_subject_categories', foreign_keys=[updated_by])

    # Relationship to track subjects associated with a subject category
    subjects: so.Mapped[List['Subject']] = so.relationship(back_populates='category')

    def __repr__(self):
        return f'<Subject Category {self.name}>'

class Subject(db.Model):
    id: so.Mapped[int] = so.mapped_column(sa.Integer, primary_key=True)
    name: so.Mapped[str] = so.mapped_column(sa.String(32), unique=True, nullable=False)
    subtext: so.Mapped[str] = so.mapped_column(sa.String(32), nullable=True)
    keywords: so.Mapped[str] = so.mapped_column(sa.String(64), nullable=True)
    notes: so.Mapped[str] = so.mapped_column(sa.Text, nullable=True)
    created_at: so.Mapped[datetime] = so.mapped_column(sa.DateTime, default=datetime.now(timezone.utc), nullable=True)
    updated_at: so.Mapped[datetime] = so.mapped_column(sa.DateTime, default=datetime.now(timezone.utc), nullable=True)
    public: so.Mapped[bool] = so.mapped_column(sa.Boolean, nullable=False)

    # Relationship to track which user created a subject
    created_by: so.Mapped[int] = so.mapped_column(sa.Integer, sa.ForeignKey('user.twitch_id'), nullable=True)
    created_by_user: so.Mapped['User'] = so.relationship('User', back_populates='subjects', foreign_keys=[created_by])

    # Relationship to track which user last updated a subject
    updated_by: so.Mapped[int] = so.mapped_column(sa.Integer, sa.ForeignKey('user.twitch_id'), nullable=True)
    updated_by_user: so.Mapped['User'] = so.relationship('User', back_populates='updated_subjects', foreign_keys=[updated_by])

    # Relationship to track subject categories associated with a subject
    category_id: so.Mapped[int] = so.mapped_column(sa.ForeignKey(SubjectCategory.id), index=True, nullable=True)
    category: so.Mapped['SubjectCategory'] = so.relationship(back_populates='subjects')

    # Relationship to track clips associated with a subject
    clips: so.Mapped[List['Clip']] = so.relationship('Clip', secondary=clip_subjects, back_populates='subjects')

    def __repr__(self):
        return f'<Subject {self.name}>'
    
class Clip(db.Model):
    id: so.Mapped[int] = so.mapped_column(sa.Integer, primary_key=True)
    twitch_id: so.Mapped[str] = so.mapped_column(sa.String(64), unique=True)
    url: so.Mapped[str] = so.mapped_column(sa.String(128))
    embed_url: so.Mapped[str] = so.mapped_column(sa.String(128))
    broadcaster_id: so.Mapped[int] = so.mapped_column(sa.Integer)
    broadcaster_name: so.Mapped[str] = so.mapped_column(sa.String(32), index=True)
    creator_id: so.Mapped[int] = so.mapped_column(sa.Integer, sa.ForeignKey('user.twitch_id'))
    creator: so.Mapped['User'] = so.relationship('User', back_populates='created_clips', foreign_keys=[creator_id])
    creator_name: so.Mapped[str] = so.mapped_column(sa.String(32), index=True)
    video_id: so.Mapped[str] = so.mapped_column(sa.String(32), nullable=True)
    game_id: so.Mapped[str] = so.mapped_column(sa.String(32), nullable=True)
    language: so.Mapped[str] = so.mapped_column(sa.String(16), nullable=True)
    title: so.Mapped[str] = so.mapped_column(sa.String(256))
    title_override: so.Mapped[str] = so.mapped_column(sa.String(256), nullable=True)
    view_count: so.Mapped[int] = so.mapped_column(sa.Integer)
    created_at: so.Mapped[str] = so.mapped_column(sa.String(32))
    thumbnail_url: so.Mapped[str] = so.mapped_column(sa.String(256))
    duration: so.Mapped[int] = so.mapped_column(sa.Integer)
    vod_offset: so.Mapped[int] = so.mapped_column(sa.Integer, nullable=True)
    is_featured: so.Mapped[bool] = so.mapped_column(sa.Boolean)
    notes: so.Mapped[str] = so.mapped_column(sa.Text, nullable=True)
    updated_at: so.Mapped[datetime] = so.mapped_column(sa.DateTime, default=datetime.now(timezone.utc), nullable=True)

    category_id: so.Mapped[int] = so.mapped_column(sa.ForeignKey(Category.id), index=True, nullable=True)
    category: so.Mapped['Category'] = so.relationship(back_populates='clips')

    status_id: so.Mapped[int] = so.mapped_column(sa.ForeignKey(Status.id), index=True, nullable=True)
    status: so.Mapped['Status'] = so.relationship(back_populates='clips')

    # Relationship to track which user last updated a clip
    updated_by: so.Mapped[int] = so.mapped_column(sa.Integer, sa.ForeignKey('user.twitch_id'), nullable=True)
    updated_by_user: so.Mapped['User'] = so.relationship('User', back_populates='updated_clips', foreign_keys=[updated_by])

    # Relationship to track users who upvoted this clip
    upvoted_by: so.Mapped[List['User']] = so.relationship('User', secondary=upvotes, back_populates='upvoted_clips')

    # Relationship to track themes associated with a clip
    themes: so.Mapped[List['Theme']] = so.relationship('Theme', secondary=clip_themes, back_populates='clips')

    # Relationship to track subjects associated with a clip
    subjects: so.Mapped[List['Subject']] = so.relationship('Subject', secondary=clip_subjects, back_populates='clips')

    def __repr__(self):
        return f"<Clip id='{self.id}' title='{self.title}' creator_name='{self.creator_name}'>"
    
class ActivityLog(db.Model):
    id: so.Mapped[int] = so.mapped_column(sa.Integer, primary_key=True)
    table_name: so.Mapped[str] = so.mapped_column(sa.String(32), nullable=False)
    row_id: so.Mapped[int] = so.mapped_column(sa.Integer, nullable=False)
    row_name: so.Mapped[str] = so.mapped_column(sa.String(32), nullable=True, default=None)
    row_twitch_id: so.Mapped[str] = so.mapped_column(sa.String(64), nullable=True, default=None)
    timestamp: so.Mapped[datetime] =  so.mapped_column(sa.DateTime, default=datetime.now(timezone.utc), nullable=False)
    action: so.Mapped[str] = so.mapped_column(sa.String(16), nullable=False)
    changes: so.Mapped[str] = so.mapped_column(sa.Text, nullable=True)
    
    # Relationship to the User who performed the action (Admin)
    admin_id: so.Mapped[int] = so.mapped_column(sa.ForeignKey(User.twitch_id), nullable=False)
    admin: so.Mapped['User'] = so.relationship(back_populates='activities')
    
    def __repr__(self):
        return f"<ActivityLog='{self.id}' timestamp='{self.timestamp}' action='{self.action}'>"