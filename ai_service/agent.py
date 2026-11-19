"""
Module that create the agent and set its parameters.
"""

import logging
import os

from google.adk.agents import Agent
from google.adk.models.lite_llm import LiteLlm
from google.adk.tools.mcp_toolset import McpToolset
from google.adk.tools.mcp_tool.mcp_session_manager import StdioConnectionParams
from mcp import StdioServerParameters
from stock_tools import STOCK_TOOLS
from grounding import SYSTEM_PROMPT, trim_tool_response

log = logging.getLogger("hbntory.agent")

product_tools = McpToolset(
    connection_params=StdioConnectionParams(
        server_params=StdioServerParameters(
            command="python",
            args=["product_server.py"],
            env={"PRODUCT_API_URL":
                 os.environ.get("PRODUCT_API_URL", "http://localhost:8000")}),
        timeout=15,
    ),
)


def log_before(tool, args, tool_context):
    log.info(f"tool call: {tool.name} {args}")
    return None


def log_after(tool, args, tool_context, tool_response):
    log.info(f"tool results: {tool.name} -> %.200s", tool_response)
    return None


root_agent = Agent(
    name="hbntory_assistant",
    model=LiteLlm(model="ollama_chat/qwen3:8b"),
    tools=[product_tools, *STOCK_TOOLS],
    instruction=SYSTEM_PROMPT,
    before_tool_callback=log_before,
    after_tool_callback=[log_after, trim_tool_response]
)
