from typing import Optional
import spotipy
from mcp.server.fastmcp import FastMCP
from .utils import get_spotify_client

# Initialize FastMCP server
mcp = FastMCP("spotify-playback")

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
        return response
    
    except Exception as e:
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