"""
This module has for only function to manualy test the MCP server.
"""

import asyncio
import os
import sys

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


async def session_for(api_url):
    """ Prepare the connection to the server with an API URL"""
    params = StdioServerParameters(
        command=sys.executable,
        args=["product_server.py"],
        env={**os.environ, "PRODUCT_API_URL": api_url}
    )

    return stdio_client(params)


async def call(api_url, tool, args):
    async with await session_for(api_url) as (read, write):
        async with ClientSession(read, write) as s:
            await s.initialize()
            res = await s.call_tool(tool, args)
            return res.isError, res.content[0].text


async def main():
    url = os.environ["PRODUCT_API_URL"]

    err, text = await call(url, "list_products", {})
    assert not err, text

    err, text = await call(url, "get_product", {"product_id": "P-001"})
    assert not err and "P-001" in text, text

    err, text = await call(url, "get_product", {"product_id": "nope"})
    assert err and "No product" in text, text

    err, text = await call("http://127.0.0.1:9", "list_product", {})
    assert err and "unavailable" in text, text
    
    print("MCP manual testing: all four checks are OK")


asyncio.run(main())
