import os
import sys
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Spotify API configuration
SPOTIFY_CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID")
SPOTIFY_CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET")
SPOTIFY_REDIRECT_URI = os.getenv("SPOTIFY_REDIRECT_URI", "http://localhost:8888/callback")

# Spotify authentication scope
SCOPE = "user-read-private user-read-email user-read-playback-state user-modify-playback-state user-read-currently-playing playlist-read-private playlist-modify-private playlist-modify-public user-top-read"

# Initialize Spotify OAuth
sp_oauth = SpotifyOAuth(
    client_id=SPOTIFY_CLIENT_ID,
    client_secret=SPOTIFY_CLIENT_SECRET,
    redirect_uri=SPOTIFY_REDIRECT_URI,
    scope=SCOPE,
    cache_path="/Users/anishagarwal/Desktop/mcp/mcp-test/.spotify_cache"
)

def get_spotify_client():
    """Get an authenticated Spotify client."""
    token_info = sp_oauth.get_cached_token()
    
    if not token_info or sp_oauth.is_token_expired(token_info):
        # Print authentication messages to stderr instead of stdout
        print("No valid token found. Please authenticate with Spotify.", file=sys.stderr)
        auth_url = sp_oauth.get_authorize_url()
        print(f"\nPlease visit this URL to authorize the application:", file=sys.stderr)
        print(f"\n{auth_url}\n", file=sys.stderr)
        
        # For MCP, we need to return a proper error message as JSON
        raise Exception("Spotify authentication required. Please run 'python test_auth.py' in your terminal to authenticate.")
    
    return spotipy.Spotify(auth=token_info['access_token']) 