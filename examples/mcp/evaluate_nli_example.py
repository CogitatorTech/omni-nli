import asyncio
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from mcp import ClientSession
from mcp.client.streamable_http import streamable_http_client
from shared import get_args


async def main():
    args = get_args(default_url="http://127.0.0.1:8000/mcp/")

    print(f"Connecting to MCP server at {args.url}...")

    try:
        async with streamable_http_client(args.url) as streams:
            async with ClientSession(streams[0], streams[1]) as session:
                await session.initialize()

                print("Connected to MCP server.")

                arguments = {
                    "premise": args.premise,
                    "hypothesis": args.hypothesis,
                    "backend": args.backend,
                    "use_reasoning": True,
                }
                if args.model:
                    arguments["model"] = args.model

                print(f"Calling evaluate_nli with backend={args.backend}...")

                result = await session.call_tool("evaluate_nli", arguments=arguments)

                print("\nResult:")
                for content in result.content:
                    if content.type == "text":
                        print(content.text)
                    else:
                        print(content)

    except Exception as e:
        print(f"MCP Error: {e}")


if __name__ == "__main__":
    asyncio.run(main())
