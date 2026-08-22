"""stdio MCP server so Cursor can call notify_merchant as a tool."""

from __future__ import annotations

import asyncio
import json
from typing import Any

import httpx
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import TextContent, Tool

NOTIFY_URL = "http://127.0.0.1:8091/tools/notify_merchant"
server = Server("gst-pulse-notify")


@server.list_tools()
async def list_tools() -> list[Tool]:
    return [
        Tool(
            name="notify_merchant",
            description="Send GST early-warning copy to a merchant on WhatsApp and email.",
            inputSchema={
                "type": "object",
                "required": ["title", "body"],
                "properties": {
                    "merchant_id": {"type": "string"},
                    "phone": {"type": "string"},
                    "email": {"type": "string"},
                    "title": {"type": "string"},
                    "body": {"type": "string"},
                    "advisor_url": {"type": "string"},
                    "gst_portal": {"type": "string"},
                },
            },
        )
    ]


@server.call_tool()
async def call_tool(name: str, arguments: dict[str, Any]):
    if name != "notify_merchant":
        raise ValueError(name)
    async with httpx.AsyncClient(timeout=15.0) as client:
        resp = await client.post(NOTIFY_URL, json=arguments)
        resp.raise_for_status()
        return [TextContent(type="text", text=json.dumps(resp.json(), indent=2))]


async def main() -> None:
    async with stdio_server() as (read, write):
        await server.run(read, write, server.create_initialization_options())


if __name__ == "__main__":
    asyncio.run(main())
