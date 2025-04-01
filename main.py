import asyncio
from mcp.server.fastmcp import FastMCP
import orchestrator

# Re-export the orchestrator's components for backward compatibility
mcp = orchestrator.mcp
get_current_track = orchestrator.get_current_track
play_track = orchestrator.play_track
control_playback = orchestrator.control_playback
get_recommendations = orchestrator.get_recommendations
analyze_playlist = orchestrator.analyze_playlist
create_ai_playlist = orchestrator.create_ai_playlist
get_top_items = orchestrator.get_top_items
analyze_track = orchestrator.analyze_track
analyze_and_recommend = orchestrator.analyze_and_recommend

# Run the server
if __name__ == "__main__":
    # Initialize and run the orchestrator
    orchestrator.mcp.run(transport='stdio')
