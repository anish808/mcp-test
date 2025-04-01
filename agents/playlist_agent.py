import json
import openai
from typing import Optional
import os
from mcp.server.fastmcp import FastMCP
from .utils import get_spotify_client

# Initialize FastMCP server
mcp = FastMCP("spotify-playlist")

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
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
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