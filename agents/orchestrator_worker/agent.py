"""
Orchestrator-Worker example: orchestrator splits, workers execute, aggregator combines.
Chat-compatible: messages state with add_messages; final assistant message appended.
"""
from typing import TypedDict, Annotated, Sequence, List, NotRequired
from operator import add as list_add
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langchain_openai import ChatOpenAI
from langchain_core.messages import AnyMessage, AIMessage, HumanMessage

llm = ChatOpenAI(model="gpt-4o-mini")


class State(TypedDict):
    messages: Annotated[Sequence[AnyMessage], add_messages]
    task: NotRequired[str]
    subtasks: NotRequired[List[str]]
    # Allow concurrent fan-in writes from workers
    results: Annotated[NotRequired[List[str]], list_add]  # type: ignore[valid-type]
    final: NotRequired[str]


def _last_user_text(state: State) -> str:
    for m in reversed(state.get("messages", [])):
        if isinstance(m, HumanMessage) or getattr(m, "type", None) == "human":
            return m.content if isinstance(m.content, str) else str(m.content)
    return state.get("task", "")


def orchestrator(state: State):
    task = state.get("task") or _last_user_text(state)
    msg = llm.invoke(
        "Break the task into 3 short, independent subtasks as bullet points.\nTask: "
        + task
    )
    lines = [l.strip("- ") for l in msg.content.splitlines() if l.strip()]
    subs = [l for l in lines if l]
    # Ensure exactly 3 slots to avoid IndexError in workers
    if not subs:
        subs = [task]
    if len(subs) < 3:
        subs = subs + [f"(Skip)" for _ in range(3 - len(subs))]
    else:
        subs = subs[:3]
    return {"subtasks": subs}


def worker_factory(idx: int):
    def _worker(state: State):
        subs = state.get("subtasks", [])
        if idx >= len(subs) or not subs[idx] or subs[idx].strip().lower() == "(skip)":
            return {}
        sub = subs[idx]
        msg = llm.invoke(f"Do this subtask succinctly: {sub}")
        # Return a single-item list; LangGraph merges with list_add
        return {"results": [msg.content]}
    return _worker


def aggregate(state: State):
    parts = [p for p in state.get("results", []) if p]
    combined = "\n\n".join(f"- {p}" for p in parts) if parts else "No results produced."
    return {"final": combined, "messages": [AIMessage(content=combined)]}


_builder = StateGraph(State)
_builder.add_node("orchestrator", orchestrator)
_builder.add_node("worker0", worker_factory(0))
_builder.add_node("worker1", worker_factory(1))
_builder.add_node("worker2", worker_factory(2))
_builder.add_node("aggregate", aggregate)

_builder.add_edge(START, "orchestrator")
_builder.add_edge("orchestrator", "worker0")
_builder.add_edge("orchestrator", "worker1")
_builder.add_edge("orchestrator", "worker2")
_builder.add_edge("worker0", "aggregate")
_builder.add_edge("worker1", "aggregate")
_builder.add_edge("worker2", "aggregate")
_builder.add_edge("aggregate", END)

app = _builder.compile()
