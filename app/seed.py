from app import db
from app.models import Rank, Status
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
    db.session.commit()

if __name__ == '__main__':
    from app import create_app
    app = create_app()
    with app.app_context():
        seed_database()
        print("Database seeded successfully.")