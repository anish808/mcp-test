from typing import Any, List, Dict, Optional
import os
import json
import asyncio
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import openai
from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP

# Load environment variables
load_dotenv()

# Initialize FastMCP server
mcp = FastMCP("spotify-ai")

# Spotify API configuration
SPOTIFY_CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID")
SPOTIFY_CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET")
SPOTIFY_REDIRECT_URI = os.getenv("SPOTIFY_REDIRECT_URI", "http://localhost:8888/callback")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Spotify authentication scope
SCOPE = "user-read-private user-read-email user-read-playback-state user-modify-playback-state user-read-currently-playing playlist-read-private playlist-modify-private playlist-modify-public user-top-read"

# Initialize Spotify client
sp_oauth = SpotifyOAuth(
    client_id=SPOTIFY_CLIENT_ID,
    client_secret=SPOTIFY_CLIENT_SECRET,
    redirect_uri=SPOTIFY_REDIRECT_URI,
    scope=SCOPE,
    cache_path="/Users/anishagarwal/Desktop/mcp/mcp-test/.spotify_cache"
)

# Helper function to get authenticated Spotify client
def get_spotify_client():
    """Get an authenticated Spotify client."""
    import sys
    
    token_info = sp_oauth.get_cached_token()
    
    if not token_info or sp_oauth.is_token_expired(token_info):
        # Print authentication messages to stderr instead of stdout
        print("No valid token found. Please authenticate with Spotify.", file=sys.stderr)
        auth_url = sp_oauth.get_authorize_url()
        print(f"\nPlease visit this URL to authorize the application:", file=sys.stderr)
        print(f"\n{auth_url}\n", file=sys.stderr)
        
        # For MCP, we need to return a proper error message as JSON
        raise Exception("Spotify authentication required. Please run 'uv run test_auth.py' in your terminal to authenticate.")
    
    return spotipy.Spotify(auth=token_info['access_token'])

# Helper function to analyze track features
async def analyze_track_features(track_features):
    """Analyze track audio features and return insights."""
    features_description = {
        "danceability": f"Danceability: {track_features['danceability']:.2f}/1.0",
        "energy": f"Energy: {track_features['energy']:.2f}/1.0",
        "valence": f"Positivity: {track_features['valence']:.2f}/1.0",
        "tempo": f"Tempo: {track_features['tempo']:.1f} BPM",
        "acousticness": f"Acousticness: {track_features['acousticness']:.2f}/1.0",
        "instrumentalness": f"Instrumentalness: {track_features['instrumentalness']:.2f}/1.0"
    }
    
    mood = "unknown"
    if track_features['valence'] > 0.7:
        if track_features['energy'] > 0.7:
            mood = "happy and energetic"
        else:
            mood = "happy and relaxed"
    elif track_features['valence'] < 0.3:
        if track_features['energy'] > 0.7:
            mood = "angry or intense"
        else:
            mood = "sad or melancholic"
    else:
        if track_features['energy'] > 0.7:
            mood = "energetic and neutral"
        else:
            mood = "calm and neutral"
    
    return {
        "features": features_description,
        "mood": mood
    }

# MCP Tools Implementation

@mcp.tool()
async def get_current_track() -> str:
    """Get information about the currently playing track on Spotify."""
    try:
        sp = get_spotify_client()
        current_track = sp.current_playback()
        
        if not current_track or not current_track.get('item'):
            return "No track is currently playing."
        
        track = current_track['item']
        artists = ", ".join([artist['name'] for artist in track['artists']])
        album = track['album']['name']
        track_name = track['name']
        
        # Format the basic response
        response = f"""
Currently Playing: "{track_name}" by {artists}
Album: {album}
Duration: {track['duration_ms'] // 60000}:{(track['duration_ms'] % 60000) // 1000:02d}
Progress: {current_track['progress_ms'] // 60000}:{(current_track['progress_ms'] % 60000) // 1000:02d}
"""
        
        # Try to get audio features, but don't fail if we can't
        try:
            track_features = sp.audio_features(track['id'])[0]
            analysis = await analyze_track_features(track_features)
            
            # Add audio analysis to the response
            response += f"""
Audio Analysis:
- {analysis['features']['danceability']}
- {analysis['features']['energy']}
- {analysis['features']['valence']}
- {analysis['features']['tempo']}
- {analysis['features']['acousticness']}

Mood: This track sounds {analysis['mood']}.
"""
        except Exception as e:
            response += "\nAudio analysis not available for this track."
        
        return response
    
    except Exception as e:
        # Return a proper error message
        return f"Error: {str(e)}"

@mcp.tool()
async def play_track(query: str) -> str:
    """Play a track on Spotify by searching for it.
    
    Args:
        query: Search query for the track (e.g., "Bohemian Rhapsody Queen")
    """
    sp = get_spotify_client()
    
    # Search for the track
    results = sp.search(q=query, type='track', limit=1)
    
    if not results['tracks']['items']:
        return f"No tracks found for query: {query}"
    
    track = results['tracks']['items'][0]
    track_uri = track['uri']
    
    # Start playback
    try:
        sp.start_playback(uris=[track_uri])
        return f"Now playing: {track['name']} by {track['artists'][0]['name']}"
    except spotipy.exceptions.SpotifyException as e:
        if e.http_status == 404:
            return "No active device found. Please open Spotify on a device first."
        return f"Error playing track: {str(e)}"

@mcp.tool()
async def control_playback(action: str) -> str:
    """Control Spotify playback with actions like play, pause, next, previous.
    
    Args:
        action: The playback control action (play, pause, next, previous)
    """
    sp = get_spotify_client()
    
    try:
        if action.lower() == "play":
            sp.start_playback()
            return "Playback started"
        elif action.lower() == "pause":
            sp.pause_playback()
            return "Playback paused"
        elif action.lower() in ["next", "skip"]:
            sp.next_track()
            return "Skipped to next track"
        elif action.lower() in ["previous", "prev"]:
            sp.previous_track()
            return "Returned to previous track"
        else:
            return f"Unknown action: {action}. Supported actions are: play, pause, next, previous"
    except spotipy.exceptions.SpotifyException as e:
        if e.http_status == 404:
            return "No active device found. Please open Spotify on a device first."
        return f"Error controlling playback: {str(e)}"

@mcp.tool()
async def get_recommendations(seed_tracks: Optional[str] = None, seed_artists: Optional[str] = None, mood: Optional[str] = None) -> str:
    """Get personalized music recommendations based on seed tracks, artists, or mood.
    
    Args:
        seed_tracks: Comma-separated track names (optional)
        seed_artists: Comma-separated artist names (optional)
        mood: Desired mood (happy, sad, energetic, relaxed, focus) (optional)
    """
    sp = get_spotify_client()
    
    # Parameters for recommendations
    params = {
        "limit": 5,
        "seed_tracks": [],
        "seed_artists": [],
        "target_valence": None,
        "target_energy": None,
        "target_tempo": None
    }
    
    # Process seed tracks if provided
    if seed_tracks:
        track_names = [t.strip() for t in seed_tracks.split(",")]
        for track_name in track_names[:2]:  # Limit to 2 seed tracks
            results = sp.search(q=track_name, type='track', limit=1)
            if results['tracks']['items']:
                params["seed_tracks"].append(results['tracks']['items'][0]['id'])
    
    # Process seed artists if provided
    if seed_artists:
        artist_names = [a.strip() for a in seed_artists.split(",")]
        for artist_name in artist_names[:2]:  # Limit to 2 seed artists
            results = sp.search(q=artist_name, type='artist', limit=1)
            if results['artists']['items']:
                params["seed_artists"].append(results['artists']['items'][0]['id'])
    
    # If no seeds provided, use user's top tracks
    if not params["seed_tracks"] and not params["seed_artists"]:
        top_tracks = sp.current_user_top_tracks(limit=2, time_range='medium_term')
        if top_tracks['items']:
            params["seed_tracks"] = [track['id'] for track in top_tracks['items']]
    
    # Process mood if provided
    if mood:
        mood = mood.lower()
        if mood == "happy":
            params["target_valence"] = 0.8
            params["target_energy"] = 0.7
        elif mood == "sad":
            params["target_valence"] = 0.2
            params["target_energy"] = 0.3
        elif mood == "energetic":
            params["target_energy"] = 0.9
            params["target_tempo"] = 140
        elif mood == "relaxed":
            params["target_energy"] = 0.3
            params["target_tempo"] = 90
        elif mood == "focus":
            params["target_energy"] = 0.5
            params["target_valence"] = 0.5
            params["target_instrumentalness"] = 0.3
    
    # Clean up params to remove None values
    clean_params = {k: v for k, v in params.items() if v is not None and (not isinstance(v, list) or len(v) > 0)}
    
    # Get recommendations
    recommendations = sp.recommendations(**clean_params)
    
    if not recommendations['tracks']:
        return "No recommendations found. Try different seed tracks or artists."
    
    # Format the response
    response = "Recommended tracks:\n\n"
    for i, track in enumerate(recommendations['tracks'], 1):
        artists = ", ".join([artist['name'] for artist in track['artists']])
        response += f"{i}. \"{track['name']}\" by {artists}\n"
        response += f"   Album: {track['album']['name']}\n"
        response += f"   Spotify URI: {track['uri']}\n\n"
    
    return response

@mcp.tool()
async def analyze_playlist(playlist_url: str) -> str:
    """Analyze a Spotify playlist and provide insights about its musical characteristics.
    
    Args:
        playlist_url: Spotify playlist URL or URI
    """
    sp = get_spotify_client()
    
    # Extract playlist ID from URL or URI
    if "spotify.com/playlist/" in playlist_url:
        playlist_id = playlist_url.split("spotify.com/playlist/")[1].split("?")[0]
    elif "spotify:playlist:" in playlist_url:
        playlist_id = playlist_url.split("spotify:playlist:")[1]
    else:
        playlist_id = playlist_url
    
    try:
        # Get playlist details
        playlist = sp.playlist(playlist_id)
        playlist_name = playlist['name']
        playlist_owner = playlist['owner']['display_name']
        track_count = playlist['tracks']['total']
        
        # Get tracks from the playlist (limited to first 100)
        tracks = []
        results = playlist['tracks']
        tracks.extend(results['items'])
        while results['next'] and len(tracks) < 100:
            results = sp.next(results)
            tracks.extend(results['items'])
        
        # Extract track IDs
        track_ids = [track['track']['id'] for track in tracks if track['track'] and track['track']['id']]
        
        # Get audio features for all tracks
        audio_features = []
        for i in range(0, len(track_ids), 50):  # Process in batches of 50
            batch = track_ids[i:i+50]
            audio_features.extend(sp.audio_features(batch))
        
        # Calculate averages
        avg_features = {
            "danceability": sum(f['danceability'] for f in audio_features if f) / len(audio_features),
            "energy": sum(f['energy'] for f in audio_features if f) / len(audio_features),
            "valence": sum(f['valence'] for f in audio_features if f) / len(audio_features),
            "tempo": sum(f['tempo'] for f in audio_features if f) / len(audio_features),
            "acousticness": sum(f['acousticness'] for f in audio_features if f) / len(audio_features),
            "instrumentalness": sum(f['instrumentalness'] for f in audio_features if f) / len(audio_features)
        }
        
        # Determine overall mood
        mood = "neutral"
        if avg_features['valence'] > 0.7:
            if avg_features['energy'] > 0.7:
                mood = "happy and energetic"
            else:
                mood = "happy and relaxed"
        elif avg_features['valence'] < 0.3:
            if avg_features['energy'] > 0.7:
                mood = "intense or aggressive"
            else:
                mood = "sad or melancholic"
        else:
            if avg_features['energy'] > 0.7:
                mood = "energetic"
            elif avg_features['energy'] < 0.3:
                mood = "calm and atmospheric"
            else:
                mood = "balanced and moderate"
        
        # Get most common artists
        artist_count = {}
        for track in tracks:
            if track['track'] and track['track']['artists']:
                artist_name = track['track']['artists'][0]['name']
                artist_count[artist_name] = artist_count.get(artist_name, 0) + 1
        
        top_artists = sorted(artist_count.items(), key=lambda x: x[1], reverse=True)[:5]
        
        # Format the response
        response = f"""
Playlist Analysis: "{playlist_name}" by {playlist_owner}
Total Tracks: {track_count}

Musical Characteristics:
- Danceability: {avg_features['danceability']:.2f}/1.0
- Energy: {avg_features['energy']:.2f}/1.0
- Positivity: {avg_features['valence']:.2f}/1.0
- Average Tempo: {avg_features['tempo']:.1f} BPM
- Acousticness: {avg_features['acousticness']:.2f}/1.0
- Instrumentalness: {avg_features['instrumentalness']:.2f}/1.0

Overall Mood: This playlist sounds {mood}.

Top Artists:
"""
        for artist, count in top_artists:
            response += f"- {artist}: {count} tracks\n"
        
        return response
    
    except Exception as e:
        return f"Error analyzing playlist: {str(e)}"

@mcp.tool()
async def create_ai_playlist(prompt: str, name: Optional[str] = None) -> str:
    """Create a Spotify playlist based on an AI-interpreted prompt.
    
    Args:
        prompt: Description of the playlist you want (e.g., "Songs for a rainy Sunday morning")
        name: Optional name for the playlist (if not provided, will be generated)
    """
    sp = get_spotify_client()
    
    # Use OpenAI to interpret the prompt and generate track suggestions
    if not OPENAI_API_KEY:
        return "OpenAI API key not configured. Please set the OPENAI_API_KEY environment variable."
    
    openai.api_key = OPENAI_API_KEY
    
    try:
        # Generate playlist concept from prompt
        concept_response = openai.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a music expert helping to create a Spotify playlist."},
                {"role": "user", "content": f"Create a concept for a playlist based on this prompt: '{prompt}'. "
                                          f"Provide a short description and suggest 10 specific songs with their artists "
                                          f"that would fit this playlist. Format as JSON with 'description' and 'tracks' fields, "
                                          f"where 'tracks' is an array of objects with 'name' and 'artist' properties."}
            ],
            response_format={"type": "json_object"}
        )
        
        playlist_concept = json.loads(concept_response.choices[0].message.content)
        
        # Generate playlist name if not provided
        if not name:
            name_response = openai.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a creative assistant helping to name a playlist."},
                    {"role": "user", "content": f"Create a catchy, concise name (max 5 words) for a playlist with this description: '{playlist_concept['description']}'"}
                ]
            )
            name = name_response.choices[0].message.content.strip().replace('"', '')
        
        # Create the playlist
        user_id = sp.me()['id']
        playlist = sp.user_playlist_create(
            user=user_id,
            name=name,
            public=False,
            description=playlist_concept['description']
        )
        
        # Search for and add tracks
        track_uris = []
        not_found = []
        
        for track_info in playlist_concept['tracks']:
            query = f"track:{track_info['name']} artist:{track_info['artist']}"
            results = sp.search(q=query, type='track', limit=1)
            
            if results['tracks']['items']:
                track_uris.append(results['tracks']['items'][0]['uri'])
            else:
                not_found.append(f"{track_info['name']} by {track_info['artist']}")
        
        # Add tracks to playlist
        if track_uris:
            sp.playlist_add_items(playlist['id'], track_uris)
        
        # Format response
        response = f"""
Created playlist: "{name}"
Description: {playlist_concept['description']}
Link: {playlist['external_urls']['spotify']}

Added {len(track_uris)} tracks to the playlist.
"""
        
        if not_found:
            response += "\nThe following tracks couldn't be found on Spotify:\n"
            for track in not_found:
                response += f"- {track}\n"
        
        return response
    
    except Exception as e:
        return f"Error creating AI playlist: {str(e)}"

@mcp.tool()
async def get_top_items(item_type: str = "tracks", time_range: str = "medium_term") -> str:
    """Get your top tracks or artists on Spotify.
    
    Args:
        item_type: Type of items to get (tracks or artists)
        time_range: Time range for the data (short_term, medium_term, long_term)
    """
    sp = get_spotify_client()
    
    if item_type not in ["tracks", "artists"]:
        return "Invalid item type. Please use 'tracks' or 'artists'."
    
    if time_range not in ["short_term", "medium_term", "long_term"]:
        return "Invalid time range. Please use 'short_term', 'medium_term', or 'long_term'."
    
    time_range_desc = {
        "short_term": "past 4 weeks",
        "medium_term": "past 6 months",
        "long_term": "several years"
    }
    
    try:
        if item_type == "tracks":
            items = sp.current_user_top_tracks(limit=10, time_range=time_range)
            response = f"Your top tracks from the {time_range_desc[time_range]}:\n\n"
            
            for i, item in enumerate(items['items'], 1):
                artists = ", ".join([artist['name'] for artist in item['artists']])
                response += f"{i}. \"{item['name']}\" by {artists}\n"
                response += f"   Album: {item['album']['name']}\n\n"
        else:  # artists
            items = sp.current_user_top_artists(limit=10, time_range=time_range)
            response = f"Your top artists from the {time_range_desc[time_range]}:\n\n"
            
            for i, item in enumerate(items['items'], 1):
                genres = ", ".join(item['genres'][:3]) if item['genres'] else "No genres listed"
                response += f"{i}. {item['name']}\n"
                response += f"   Genres: {genres}\n"
                response += f"   Popularity: {item['popularity']}/100\n\n"
        
        return response
    
    except Exception as e:
        return f"Error getting top {item_type}: {str(e)}"

# Run the server
if __name__ == "__main__":
    # Initialize and run the server
    mcp.run(transport='stdio')
