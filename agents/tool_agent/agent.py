"""
Tool-using agent example with a minimal calculator tool.
Chat-compatible: messages state with add_messages; final assistant message appended.
"""
from typing import TypedDict, Annotated, Sequence
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langchain_openai import ChatOpenAI
from langchain_core.messages import AnyMessage, AIMessage, HumanMessage
from langchain_core.tools import tool

llm = ChatOpenAI(model="gpt-4o-mini")


@tool
def calculator(expression: str) -> str:
    """Evaluate a basic Python arithmetic expression, e.g., '2 + 2 * 3'."""
    try:
        # Extremely limited, eval used only for demo arithmetic
        return str(eval(expression, {"__builtins__": {}}, {}))
    except Exception as e:
        return f"calc error: {e}"


class State(TypedDict):
    messages: Annotated[Sequence[AnyMessage], add_messages]
    query: str
    answer: str


def _last_user_text(state: State) -> str:
    for m in reversed(state.get("messages", [])):
        if isinstance(m, HumanMessage) or getattr(m, "type", None) == "human":
            return m.content if isinstance(m.content, str) else str(m.content)
    return state.get("query", "")


def agent_node(state: State):
    query = state.get("query") or _last_user_text(state)
    # Very simple tool-use heuristic
    if any(ch.isdigit() for ch in query) and any(op in query for op in ["+","-","*","/"]):
        result = calculator.invoke({"expression": query})
        final = f"Result: {result}"
    else:
        final = llm.invoke(query).content
    return {"answer": final, "messages": [AIMessage(content=final)]}


_builder = StateGraph(State)
_builder.add_node("agent", agent_node)
_builder.add_edge(START, "agent")
_builder.add_edge("agent", END)

app = _builder.compile()
