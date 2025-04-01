from typing import Optional
from mcp.server.fastmcp import FastMCP
from .utils import get_spotify_client

# Initialize FastMCP server
mcp = FastMCP("spotify-insights")

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