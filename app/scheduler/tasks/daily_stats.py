from app import db
from app.models import Statistics, Clip, User, Status, upvotes
from datetime import datetime, timezone

def update_daily_stats():
    """Calculate and store daily statistics."""
    date = datetime.now(timezone.utc).date()
    total_clips = Clip.query.count()
    unsorted_clips = Clip.query.filter(Clip.status_id == 1).count()
    clips_without_subjects = Clip.query.join(Status, Clip.status_id == Status.id).filter(Status.type != 'Hidden', Clip.subjects == None).count()
    clips_without_themes = Clip.query.join(Status, Clip.status_id == Status.id).filter(Status.type != 'Hidden', Clip.themes == None).count()
    clips_without_category = Clip.query.join(Status, Clip.status_id == Status.id).filter(Status.type != 'Hidden', Clip.category_id == None).count()
    clips_without_layout = Clip.query.join(Status, Clip.status_id == Status.id).filter(Status.type != 'Hidden', Clip.layout_id == None).count()
    total_views = db.session.query(db.func.sum(Clip.view_count)).scalar() or 0
    total_upvotes = db.session.query(upvotes).count()
    total_verified_users = User.query.filter(User.last_verified != None).count()
    unique_broadcasters = db.session.query(Clip.broadcaster_id).distinct().count()
    unique_clippers = db.session.query(Clip.creator_id).distinct().count()

    stats = Statistics(
        date=date,
        total_clips=total_clips,
        unsorted_clips=unsorted_clips,
        clips_without_subjects=clips_without_subjects,
        clips_without_themes=clips_without_themes,
        clips_without_category=clips_without_category,
        clips_without_layout=clips_without_layout,
        total_views=total_views,
        total_upvotes=total_upvotes,
        total_verified_users=total_verified_users,
        unique_broadcasters=unique_broadcasters,
        unique_clippers=unique_clippers
    )
    db.session.add(stats)
    db.session.commit()