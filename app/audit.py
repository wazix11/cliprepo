import json
from sqlalchemy import event, insert
from sqlalchemy.orm.attributes import get_history
from app import db
from app.models import *

def get_current_user_id():
    from flask_login import current_user
    try:
        return current_user.id if current_user.is_authenticated else 'system'
    except AttributeError:
        return 'system'

def activity_log_listener(mapper, connection, target, action):
    changes = {}
    for attr in target.__mapper__.columns:
        hist = get_history(target, attr.key)
        if hist.has_changes():
            changes[attr.key] = {
                'old': hist.deleted[0] if hist.deleted else None,
                'new': hist.added[0] if hist.added else None
            }

    # Only log User updates if certain fields changed
    if (
        action == 'update'
        and target.__tablename__ == 'user'
        and not set(changes.keys()) & {'notes', 'login_enabled', 'updated_at', 'rank_id', 'updated_by'}
    ):
        return
    
    if action == 'update' and not changes:
        return
    
    log = insert(ActivityLog).values(
        table_name=target.__tablename__,
        row_id=str(getattr(target, 'id', None)),
        row_name=str(getattr(target, 'name', None)),
        row_twitch_id=str(getattr(target, 'twitch_id', None)),
        action=action,
        admin_id=get_current_user_id(),
        changes= json.dumps(changes, default=str) if changes else None
    )
    connection.execute(log)

def after_insert_listener(mapper, connection, target):
    activity_log_listener(mapper, connection, target, 'insert')

def after_update_listener(mapper, connection, target):
    activity_log_listener(mapper, connection, target, 'update')

def after_delete_listener(mapper, connection, target):
    activity_log_listener(mapper, connection, target, 'delete')

def register_audit_listeners():
    for mapper in db.Model.registry.mappers:
        cls = mapper.class_
        if hasattr(cls, '__tablename__'):
            event.listen(cls, 'after_insert', after_insert_listener)
            event.listen(cls, 'after_update', after_update_listener)
            event.listen(cls, 'after_delete', after_delete_listener)