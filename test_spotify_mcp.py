import asyncio
import inspect
from main import mcp, get_current_track, get_recommendations

async def test_server():
    print("Testing get_current_track...")
    result = await get_current_track()
    print(result)
    
    # Uncomment to test other functions
    # print("\nTesting get_recommendations...")
    # result = await get_recommendations(seed_artists="Coldplay")
    # print(result)

if __name__ == "__main__":
    asyncio.run(test_server()) 