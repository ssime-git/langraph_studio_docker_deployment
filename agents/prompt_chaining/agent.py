"""
Prompt chaining example: outline -> draft -> edit.
Chat-compatible: messages state with add_messages; final assistant response appended.
"""
from typing import TypedDict, Annotated, Sequence, NotRequired
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langchain_openai import ChatOpenAI
from langchain_core.messages import AnyMessage, AIMessage, HumanMessage

llm = ChatOpenAI(model="gpt-4o-mini")


class State(TypedDict):
    messages: Annotated[Sequence[AnyMessage], add_messages]
    topic: NotRequired[str]
    outline: NotRequired[str]
    draft: NotRequired[str]
    final: NotRequired[str]


def _last_user_text(state: State) -> str:
    for m in reversed(state.get("messages", [])):
        if isinstance(m, HumanMessage) or getattr(m, "type", None) == "human":
            return m.content if isinstance(m.content, str) else str(m.content)
    return state.get("topic", "")


def make_outline(state: State):
    topic = state.get("topic") or _last_user_text(state)
    msg = llm.invoke(f"Create a concise outline for an article about {topic}.")
    return {"outline": msg.content}


def write_draft(state: State):
    msg = llm.invoke(
        "Write a brief article following this outline:\n" + state["outline"]
    )
    return {"draft": msg.content}


def edit_draft(state: State):
    msg = llm.invoke(
        "Improve the clarity and structure of the following draft; return the improved version only:\n" + state["draft"]
    )
    return {"final": msg.content, "messages": [AIMessage(content=msg.content)]}


_builder = StateGraph(State)
_builder.add_node("make_outline", make_outline)
_builder.add_node("write_draft", write_draft)
_builder.add_node("edit_draft", edit_draft)

_builder.add_edge(START, "make_outline")
_builder.add_edge("make_outline", "write_draft")
_builder.add_edge("write_draft", "edit_draft")
_builder.add_edge("edit_draft", END)

app = _builder.compile()
