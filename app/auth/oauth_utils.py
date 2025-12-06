import os, requests
from datetime import datetime, timezone, timedelta
from dotenv import load_dotenv
from app import db
from app.models import User

load_dotenv(override=True)
TWITCH_CLIENT_ID = os.environ.get('TWITCH_CLIENT_ID')
TWITCH_CLIENT_SECRET = os.environ.get('TWITCH_CLIENT_SECRET')
TWITCH_TOKEN_URL = 'https://id.twitch.tv/oauth2/token'
TWITCH_VALIDATE_URL = 'https://id.twitch.tv/oauth2/validate'

class ExpiredAccessTokenError(Exception):
    """Raised when an access token has expired and cannot be refreshed."""
    pass

def validate_access_token(access_token):
    """Validate a Twitch access token."""
    headers = {'Authorization': f'OAuth {access_token}'}
    response = requests.get(TWITCH_VALIDATE_URL, headers=headers)

    if response.status_code == 401:
        return None
    
    return response.json() if response.ok else None

def refresh_user_access_token(user, force_refresh=False):
    """
    Refresh a user's access token if needed.
    
    Args:
        user: The User object
        force_refresh: Force refresh even if token is still valid
        
    Returns:
        bool: True if token was refreshed, False if still valid
        
    Raises:
        ExpiredAccessTokenError: If token refresh fails
    """
    if not user.access_token or not user.refresh_token:
        raise ExpiredAccessTokenError("No tokens available")
    
    now = datetime.now(timezone.utc)
    
    # Check token once per hour unless forced
    if not force_refresh and user.last_verified:
        last_verified = user.last_verified.replace(tzinfo=timezone.utc) if user.last_verified.tzinfo is None else user.last_verified
        if last_verified > now - timedelta(hours=1):
            return False

    # Force refresh if within 1 hour of expiry
    if user.expires_at:
        expires_at = user.expires_at.replace(tzinfo=timezone.utc) if user.expires_at.tzinfo is None else user.expires_at
        if expires_at < now + timedelta(hours=1):
            force_refresh = True
        
    # Validate current token first (unless forcing)
    if not force_refresh:
        validation = validate_access_token(user.access_token)
        if validation:
            # Token is still valid, update verification time
            user.last_verified = now
            db.session.commit()
            return False
    
    # Token needs refresh
    params = {
        'client_id': TWITCH_CLIENT_ID,
        'client_secret': TWITCH_CLIENT_SECRET,
        'grant_type': 'refresh_token',
        'refresh_token': user.refresh_token
    }

    response = requests.post(TWITCH_TOKEN_URL, data=params)

    if response.status_code != 200:
        raise ExpiredAccessTokenError("Failed to refresh token")
    
    data = response.json()

    # Update user tokens
    user.access_token = data.get('access_token')
    user.refresh_token = data.get('refresh_token', user.refresh_token)
    user.token_scope = data.get('scope', '').replace(',', ' ')

    # Calculate expiration (3600 seconds for Twitch)
    expires_in = data.get('expires_in', 3600)
    user.expires_at = now + timedelta(seconds=expires_in)
    user.last_verified = now

    db.session.commit()
    return True

def require_scopes(user, required_scopes):
    """
    Check if a user has the required OAuth scopes.
    
    Args:
        user: The User object
        required_scopes: List of required scope strings
        
    Returns:
        tuple: (bool, list) - (has_all_scopes, missing_scopes)
    """
    if not user.token_scope:
        return False, required_scopes
    
    user_scopes = set(user.token_scope.split())
    missing = [scope for scope in required_scopes if scope not in user_scopes]
    
    return len(missing) == 0, missing