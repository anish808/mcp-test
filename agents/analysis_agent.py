from mcp.server.fastmcp import FastMCP
from .utils import get_spotify_client

# Initialize FastMCP server
mcp = FastMCP("spotify-analysis")

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

@mcp.tool()
async def analyze_track(track_id_or_name: str) -> str:
    """Analyze audio features of a track and provide insights.
    
    Args:
        track_id_or_name: Spotify track ID or track name to search
    """
    sp = get_spotify_client()
    
    # Determine if input is a track ID or name
    if track_id_or_name.startswith("spotify:track:") or (len(track_id_or_name) == 22 and all(c in "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz" for c in track_id_or_name)):
        track_id = track_id_or_name.split(":")[-1] if ":" in track_id_or_name else track_id_or_name
        try:
            track = sp.track(track_id)
        except:
            return f"Invalid track ID: {track_id_or_name}"
    else:
        # Search for the track
        results = sp.search(q=track_id_or_name, type='track', limit=1)
        if not results['tracks']['items']:
            return f"No track found for query: {track_id_or_name}"
        track = results['tracks']['items'][0]
        track_id = track['id']
    
    # Get audio features
    try:
        track_features = sp.audio_features(track_id)[0]
        if not track_features:
            return f"No audio features available for track: {track['name']}"
        
        analysis = await analyze_track_features(track_features)
        
        # Format response
        artists = ", ".join([artist['name'] for artist in track['artists']])
        response = f"""
Track Analysis: "{track['name']}" by {artists}
Album: {track['album']['name']}

Audio Features:
- {analysis['features']['danceability']}
- {analysis['features']['energy']}
- {analysis['features']['valence']}
- {analysis['features']['tempo']}
- {analysis['features']['acousticness']}
- {analysis['features']['instrumentalness']}

Mood: This track sounds {analysis['mood']}.

Key: {['C', 'C♯/D♭', 'D', 'D♯/E♭', 'E', 'F', 'F♯/G♭', 'G', 'G♯/A♭', 'A', 'A♯/B♭', 'B'][track_features['key']]} {['Minor', 'Major'][track_features['mode']]}
Time Signature: {track_features['time_signature']}/4
"""
        return response
    
    except Exception as e:
        return f"Error analyzing track: {str(e)}" 