import os
from dotenv import load_dotenv
import spotipy
from spotipy.oauth2 import SpotifyOAuth

# Load environment variables
load_dotenv()

# Spotify API configuration
SPOTIFY_CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID")
SPOTIFY_CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET")
SPOTIFY_REDIRECT_URI = os.getenv("SPOTIFY_REDIRECT_URI", "http://localhost:8888/callback")

# Spotify authentication scope
SCOPE = "user-read-private user-read-email user-read-playback-state user-modify-playback-state user-read-currently-playing playlist-read-private playlist-modify-private playlist-modify-public user-top-read"

def test_spotify_auth():
    print("Testing Spotify Authentication")
    
    # Check if credentials are set
    if not SPOTIFY_CLIENT_ID or not SPOTIFY_CLIENT_SECRET:
        print("ERROR: Spotify credentials not found in .env file")
        print("Please make sure you have set SPOTIFY_CLIENT_ID and SPOTIFY_CLIENT_SECRET")
        return
    
    print(f"Using redirect URI: {SPOTIFY_REDIRECT_URI}")
    
    # Initialize Spotify OAuth
    sp_oauth = SpotifyOAuth(
        client_id=SPOTIFY_CLIENT_ID,
        client_secret=SPOTIFY_CLIENT_SECRET,
        redirect_uri=SPOTIFY_REDIRECT_URI,
        scope=SCOPE,
        cache_path=".spotify_cache"
    )
    
    # Check for cached token
    token_info = sp_oauth.get_cached_token()
    
    if token_info and not sp_oauth.is_token_expired(token_info):
        print("Found valid cached token")
        
        # Test the token with a simple API call
        sp = spotipy.Spotify(auth=token_info['access_token'])
        try:
            user_info = sp.current_user()
            print(f"Successfully authenticated as: {user_info['display_name']} ({user_info['id']})")
        except Exception as e:
            print(f"Error using cached token: {e}")
            token_info = None
    
    # If no valid token, start authentication flow
    if not token_info or sp_oauth.is_token_expired(token_info):
        print("No valid token found. Starting authentication flow...")
        auth_url = sp_oauth.get_authorize_url()
        print(f"\nPlease visit this URL to authorize the application:")
        print(f"\n{auth_url}\n")
        
        response = input("Enter the URL you were redirected to: ")
        code = sp_oauth.parse_response_code(response)
        
        try:
            token_info = sp_oauth.get_access_token(code)
            print("Successfully obtained new access token")
            
            # Test the new token
            sp = spotipy.Spotify(auth=token_info['access_token'])
            user_info = sp.current_user()
            print(f"Successfully authenticated as: {user_info['display_name']} ({user_info['id']})")
        except Exception as e:
            print(f"Error during authentication: {e}")
            return
    
    # Test a few API endpoints to verify scopes
    sp = spotipy.Spotify(auth=token_info['access_token'])
    
    print("\nTesting API endpoints:")
    
    try:
        current_track = sp.current_playback()
        if current_track:
            print("✓ Successfully retrieved current playback")
            if current_track.get('item'):
                track = current_track['item']
                print(f"   Currently playing: {track['name']} by {track['artists'][0]['name']}")
        else:
            print("✓ No active playback found (this is normal if nothing is playing)")
    except Exception as e:
        print(f"✗ Error retrieving current playback: {e}")
    
    try:
        top_tracks = sp.current_user_top_tracks(limit=1)
        if top_tracks and top_tracks['items']:
            track = top_tracks['items'][0]
            print(f"✓ Successfully retrieved top track: {track['name']} by {track['artists'][0]['name']}")
        else:
            print("✓ No top tracks found")
    except Exception as e:
        print(f"✗ Error retrieving top tracks: {e}")
    
    print("\nAuthentication test complete")

if __name__ == "__main__":
    test_spotify_auth() 