import asyncio
from orchestrator import mcp, control_playback, play_track

async def test_server():
    print("Testing basic Spotify controls...")
    
    # Test playback control
    try:
        print("\nTesting playback control (pause)...")
        result = await control_playback("pause")
        print(result)
        
        print("\nWaiting 2 seconds...")
        await asyncio.sleep(2)
        
        print("\nTesting playback control (play)...")
        result = await control_playback("play")
        print(result)
    except Exception as e:
        print(f"Error testing playback control: {e}")
    
    # Test playing a specific track
    try:
        print("\nTesting play_track...")
        result = await play_track("Bohemian Rhapsody Queen")
        print(result)
    except Exception as e:
        print(f"Error testing play_track: {e}")

if __name__ == "__main__":
    asyncio.run(test_server()) 