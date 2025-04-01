from typing import Optional
import spotipy
from mcp.server.fastmcp import FastMCP
from .utils import get_spotify_client

# Initialize FastMCP server
mcp = FastMCP("spotify-discovery")

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