from app import db
from app.models import Rank, Status, User
from datetime import datetime, timezone

def seed_database():
    if db.session.query(Rank).count() == 0:
        ranks = [
            Rank(name='USER'),
            Rank(name='MODERATOR'),
            Rank(name='ADMIN'),
            Rank(name='SUPERADMIN')
        ]
        db.session.add_all(ranks)

    if db.session.query(Status).count() == 0:
        default_status = Status(name='Unsorted',
                                type='Pending',
                                color='#ff8040',
                                created_at=datetime.now(timezone.utc)
                                )
        db.session.add(default_status)

    if not db.session.query(User).filter_by(twitch_id='system').first():
        system_user = User(
            twitch_id='system',
            login='system',
            display_name='System',
            profile_image_url='',
            contributions=0,
            last_verified=datetime.now(timezone.utc),
            access_token=None,
            refresh_token=None,
            notes='System user for automated actions',
            login_enabled=False,
            updated_at=datetime.now(timezone.utc),
            rank_id=4
        )
        db.session.add(system_user)

    db.session.commit()

if __name__ == '__main__':
    from app import create_app
    app = create_app()
    with app.app_context():
        seed_database()
        print("Database seeded successfully.")