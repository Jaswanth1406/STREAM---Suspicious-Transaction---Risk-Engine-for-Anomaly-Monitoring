"""
STREAM Agent — LangGraph ReAct Agent Orchestrator.

Assembles the LLM, tools, and system prompt into a LangGraph ReAct agent.
Exposes `invoke()` and `astream_events()` for sync and streaming use.
"""

from __future__ import annotations

from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langgraph.prebuilt import create_react_agent

from agent.llm import get_llm
from agent.prompts import SYSTEM_PROMPT
from agent.tools.sql_query import query_database
from agent.tools.risk_explainer import explain_tender_risk
from agent.tools.vendor_lookup import investigate_vendor
from agent.tools.ml_predict import predict_tender_risk
from agent.tools.report_gen import generate_audit_report
from agent.tools.network_analysis import analyze_network

# All tools available to the agent
TOOLS = [
    query_database,
    explain_tender_risk,
    investigate_vendor,
    predict_tender_risk,
    generate_audit_report,
    analyze_network,
]

# Module-level singleton (lazy init)
_agent = None


def _get_agent():
    """Lazy-initialise the LangGraph agent on first use."""
    global _agent
    if _agent is None:
        llm = get_llm(temperature=0)
        _agent = create_react_agent(
            model=llm,
            tools=TOOLS,
            prompt=SYSTEM_PROMPT,
        )
    return _agent


def invoke(messages: list[dict]) -> dict:
    """
    Run the agent synchronously.

    Parameters
    ----------
    messages : list[dict]
        Conversation history in OpenAI format:
        [{"role": "user", "content": "..."}, ...]

    Returns
    -------
    dict
        {"response": str, "tool_calls": list[dict]}
    """
    agent = _get_agent()

    # Convert dict messages to LangChain message objects
    lc_messages = []
    for m in messages:
        role = m.get("role", "user")
        content = m.get("content", "")
        if role == "user":
            lc_messages.append(HumanMessage(content=content))
        elif role == "assistant":
            lc_messages.append(AIMessage(content=content))
        elif role == "system":
            lc_messages.append(SystemMessage(content=content))

    result = agent.invoke({"messages": lc_messages})

    # Extract final response and tool calls
    all_messages = result.get("messages", [])
    response_text = ""
    tool_calls_log = []

    for msg in all_messages:
        # Collect tool call info for transparency
        if hasattr(msg, "tool_calls") and msg.tool_calls:
            for tc in msg.tool_calls:
                tool_calls_log.append({
                    "tool": tc.get("name", ""),
                    "args": tc.get("args", {}),
                })
        # The last AI message is the final answer
        if isinstance(msg, AIMessage) and msg.content and not getattr(msg, "tool_calls", None):
            response_text = msg.content

    # Fallback: if no clean AI message, take the very last message content
    if not response_text and all_messages:
        last = all_messages[-1]
        if hasattr(last, "content"):
            response_text = last.content

    return {
        "response": response_text,
        "tool_calls": tool_calls_log,
    }


async def astream_events(messages: list[dict]):
    """
    Async generator that yields SSE-formatted events from the agent.

    Yields
    ------
    str
        Server-Sent Event lines: "data: {...}\n\n"
    """
    import json

    agent = _get_agent()

    lc_messages = []
    for m in messages:
        role = m.get("role", "user")
        content = m.get("content", "")
        if role == "user":
            lc_messages.append(HumanMessage(content=content))
        elif role == "assistant":
            lc_messages.append(AIMessage(content=content))
        elif role == "system":
            lc_messages.append(SystemMessage(content=content))

    async for event in agent.astream_events(
        {"messages": lc_messages}, version="v2"
    ):
        kind = event.get("event", "")

        if kind == "on_chat_model_stream":
            # Token-by-token streaming
            chunk = event.get("data", {}).get("chunk")
            if chunk and hasattr(chunk, "content") and chunk.content:
                yield f"data: {json.dumps({'type': 'token', 'content': chunk.content})}\n\n"

        elif kind == "on_tool_start":
            tool_name = event.get("name", "")
            tool_input = event.get("data", {}).get("input", "")
            yield f"data: {json.dumps({'type': 'tool_start', 'tool': tool_name, 'input': str(tool_input)[:200]})}\n\n"

        elif kind == "on_tool_end":
            tool_name = event.get("name", "")
            output = event.get("data", {}).get("output", "")
            # Truncate long tool outputs for SSE
            output_str = str(output)[:500] if output else ""
            yield f"data: {json.dumps({'type': 'tool_end', 'tool': tool_name, 'output_preview': output_str})}\n\n"

    yield f"data: {json.dumps({'type': 'done'})}\n\n"
