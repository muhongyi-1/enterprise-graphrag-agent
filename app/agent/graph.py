from langgraph.graph import (
    StateGraph,
    START
)

from langgraph.prebuilt import (
    ToolNode,
    tools_condition
)

from langgraph.checkpoint.memory import (
    InMemorySaver
)

from app.agent.state import (
    AgentState
)

from app.agent.nodes import (
    agent_node,
    tools
)


builder = StateGraph(
    AgentState
)

builder.add_node(
    "agent",
    agent_node
)

tool_node = ToolNode(
    tools
)

builder.add_node(
    "tools",
    tool_node
)

builder.add_edge(
    START,
    "agent"
)

builder.add_conditional_edges(
    "agent",
    tools_condition
)

builder.add_edge(
    "tools",
    "agent"
)

checkpointer = (
    InMemorySaver()
)

graph = builder.compile(
    checkpointer=checkpointer
)