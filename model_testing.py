import os
os.environ['DATABASE_URL'] = 'sqlite://'

from datetime import datetime, timezone, timedelta
import unittest, pytz
from app import create_app, db
from app.models import *
from config import Config

class TestConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite://'  # Use an in-memory SQLite database

class ModelTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app(TestConfig)
        self.app_context = self.app.app_context()
        self.app_context.push()

        # Make sure to use an in-memory database for the tests
        self.assertEqual(self.app.config['SQLALCHEMY_DATABASE_URI'], 'sqlite://')

        db.create_all()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    # Test User creation and defaults
    def test_create_user(self):
        rank = Rank(name='Member')
        user = User(id='123', 
                    login='test_login', 
                    display_name='test_user', 
                    profile_image_url='test_url', 
                    rank=rank)

        db.session.add(rank)
        db.session.add(user)
        db.session.commit()

        queried_user = db.session.get(User, '123')
        self.assertIsNotNone(queried_user)
        self.assertEqual(queried_user.login, 'test_login')
        self.assertEqual(queried_user.display_name, 'test_user')
        self.assertEqual(queried_user.profile_image_url, 'test_url')
        self.assertEqual(queried_user.rank.name, 'Member')
        self.assertEqual(queried_user.contributions, 0)  # Test default value
    
    # Test Clip and Theme many-to-many relationship
    def test_clip_themes_relationship(self):
        theme = Theme(name='Horror')
        theme2 = Theme(name='Comedy')
        clip = Clip(id='clip1', 
                    url='url1', 
                    embed_url='embed1', 
                    broadcaster_id='b_id1', 
                    broadcaster_name='broadcast1', 
                    creator_id='c_id1',
                    creator_name='creator1',
                    game_id='game1',
                    language='en',
                    title='Scary Clip', 
                    view_count='201',
                    created_at='created',
                    thumbnail_url='thumbnail',
                    duration='30',
                    is_featured=1
                    )
        clip.themes.append(theme)
        clip.themes.append(theme2)

        db.session.add(theme)
        db.session.add(theme2)
        db.session.add(clip)
        db.session.commit()

        queried_clip = db.session.get(Clip, 'clip1')
        self.assertIn(theme, queried_clip.themes)
        self.assertIn(theme2, queried_clip.themes)
        self.assertIn(clip, theme.clips)
        self.assertIn(clip, theme2.clips)
    
    # Test User upvoting a Clip (Many-to-Many relationship)
    def test_user_upvote_clip(self):
        user = User(id='123', 
                    login='test_login', 
                    display_name='test_user', 
                    profile_image_url='test_url')
        user2 = User(id='223', 
                    login='test_login2', 
                    display_name='test_user2', 
                    profile_image_url='test_url2')
        clip = Clip(id='clip1', 
                    url='url1', 
                    embed_url='embed1', 
                    broadcaster_id='b_id1', 
                    broadcaster_name='broadcast1', 
                    creator_id='c_id1',
                    creator_name='creator1',
                    game_id='game1',
                    language='en',
                    title='Scary Clip', 
                    view_count='201',
                    created_at='created',
                    thumbnail_url='thumbnail',
                    duration='30',
                    is_featured=1
                    )
        user.upvoted_clips.append(clip)
        user2.upvoted_clips.append(clip)

        db.session.add(user)
        db.session.add(user2)
        db.session.add(clip)
        db.session.commit()

        queried_clip = db.session.get(Clip, 'clip1')
        queried_user = db.session.get(User, '123')
        queried_user2 = db.session.get(User, '223')

        self.assertIn(clip, queried_user.upvoted_clips)
        self.assertIn(clip, queried_user2.upvoted_clips)
        self.assertIn(user, queried_clip.upvoted_by)
        self.assertIn(user2, queried_clip.upvoted_by)

    # Test foreign key relationship between Clip and Category
    def test_clip_category_relationship(self):
        category = Category(name='Action')
        clip = Clip(id='clip1', 
                    url='url1', 
                    embed_url='embed1', 
                    broadcaster_id='b_id1', 
                    broadcaster_name='broadcast1', 
                    creator_id='c_id1',
                    creator_name='creator1',
                    game_id='game1',
                    language='en',
                    title='Scary Clip', 
                    view_count='201',
                    created_at='created',
                    thumbnail_url='thumbnail',
                    duration='30',
                    is_featured=1, 
                    category=category)

        db.session.add(category)
        db.session.add(clip)
        db.session.commit()

        queried_clip = db.session.get(Clip, 'clip1')
        self.assertEqual(queried_clip.category.name, 'Action')
        self.assertIn(clip, category.clips)
    
    # Test Rank uniqueness constraint
    def test_rank_uniqueness(self):
        rank1 = Rank(name='Member')
        rank2 = Rank(name='Member')  # Duplicate name, should raise IntegrityError

        db.session.add(rank1)
        db.session.commit()

        with self.assertRaises(sa.exc.IntegrityError):
            db.session.add(rank2)
            db.session.commit()

if __name__ == '__main__':
    unittest.main(verbosity=2)