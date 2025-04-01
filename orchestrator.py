from mcp.server.fastmcp import FastMCP
from agents import playback_agent, discovery_agent, playlist_agent, insights_agent, analysis_agent

# Initialize FastMCP server
mcp = FastMCP("spotify-orchestrator")

@mcp.tool()
async def get_current_track() -> str:
    """Get information about the currently playing track on Spotify."""
    # Forward to playback agent
    return await playback_agent.get_current_track()

@mcp.tool()
async def play_track(query: str) -> str:
    """Play a track on Spotify by searching for it."""
    return await playback_agent.play_track(query)

@mcp.tool()
async def control_playback(action: str) -> str:
    """Control Spotify playback with actions like play, pause, next, previous."""
    return await playback_agent.control_playback(action)

@mcp.tool()
async def get_recommendations(seed_tracks: str = None, seed_artists: str = None, mood: str = None) -> str:
    """Get personalized music recommendations."""
    return await discovery_agent.get_recommendations(seed_tracks, seed_artists, mood)

@mcp.tool()
async def analyze_playlist(playlist_url: str) -> str:
    """Analyze a Spotify playlist and provide insights."""
    return await playlist_agent.analyze_playlist(playlist_url)

@mcp.tool()
async def create_ai_playlist(prompt: str, name: str = None) -> str:
    """Create a Spotify playlist based on an AI-interpreted prompt."""
    return await playlist_agent.create_ai_playlist(prompt, name)

@mcp.tool()
async def get_top_items(item_type: str = "tracks", time_range: str = "medium_term") -> str:
    """Get your top tracks or artists on Spotify."""
    return await insights_agent.get_top_items(item_type, time_range)

@mcp.tool()
async def analyze_track(track_id_or_name: str) -> str:
    """Analyze audio features of a track and provide insights."""
    return await analysis_agent.analyze_track(track_id_or_name)

# Advanced cross-agent tools
@mcp.tool()
async def analyze_and_recommend(track_id_or_name: str) -> str:
    """Analyze a track and find similar recommendations."""
    # First analyze the track
    analysis_result = await analysis_agent.analyze_track(track_id_or_name)
    
    # Extract track name for recommendation
    if "Track Analysis:" in analysis_result:
        track_name = analysis_result.split("Track Analysis: \"")[1].split("\"")[0]
        # Get recommendations based on this track
        recommendations = await discovery_agent.get_recommendations(seed_tracks=track_name)
        return f"{analysis_result}\n\n--- SIMILAR TRACKS ---\n\n{recommendations}"
    else:
        return f"Could not analyze track. {analysis_result}" 