import asyncio
import sys
import inspect
from main import mcp
import main

async def run_tool(tool_func, **kwargs):
    try:
        result = await tool_func(**kwargs)
        print("\nResult:")
        print(result)
    except Exception as e:
        print(f"Error: {e}")

async def main_interactive():
    print("Spotify MCP Interactive Tester")
    
    # Get all tool functions from the main module
    tool_functions = {}
    for name, obj in inspect.getmembers(main):
        if inspect.iscoroutinefunction(obj) and hasattr(obj, '_mcp_tool_metadata'):
            tool_functions[name] = obj
    
    print("Available tools:")
    for name in tool_functions:
        print(f"- {name}")
    
    while True:
        print("\nEnter a tool name to test (or 'exit' to quit):")
        tool_name = input("> ")
        
        if tool_name.lower() == 'exit':
            break
        
        if tool_name not in tool_functions:
            print(f"Tool '{tool_name}' not found.")
            continue
        
        tool_func = tool_functions[tool_name]
        
        # Get the function signature to determine parameters
        sig = inspect.signature(tool_func)
        params = {}
        
        # Skip self or cls parameter if it's a method
        param_items = list(sig.parameters.items())
        if param_items and param_items[0][0] in ('self', 'cls'):
            param_items = param_items[1:]
        
        if param_items:
            print(f"Enter parameters for {tool_name}:")
            for param_name, param in param_items:
                if param.default is inspect.Parameter.empty:
                    # Required parameter
                    while True:
                        value = input(f"{param_name} (required): ")
                        if value:
                            params[param_name] = value
                            break
                        print("This parameter is required.")
                else:
                    # Optional parameter
                    value = input(f"{param_name} (optional, default={param.default}): ")
                    if value:
                        params[param_name] = value
        
        await run_tool(tool_func, **params)

if __name__ == "__main__":
    asyncio.run(main_interactive()) 