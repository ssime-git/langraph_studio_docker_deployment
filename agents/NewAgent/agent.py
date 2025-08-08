# agent.py
from typing import TypedDict, Annotated, List
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
from langchain_core.messages import AIMessage, HumanMessage, BaseMessage

class State(TypedDict):
    # Strongly typed messages so schema includes LC message structure
    messages: Annotated[List[BaseMessage], add_messages]

def agent_node(state: State):
    last_user = None
    # Handle both LC messages and dicts defensively
    for m in reversed(state["messages"]):
        if isinstance(m, HumanMessage):
            last_user = m.content
            break
        if isinstance(m, dict) and m.get("role") == "user":
            last_user = m.get("content", "")
            break
    reply = f"Echo: {last_user}" if last_user else "Hello from echo agent"
    return {"messages": [AIMessage(content=reply)]}

graph = StateGraph(State)
graph.add_node("agent", agent_node)
graph.set_entry_point("agent")
graph.add_edge("agent", END)
app = graph.compile()