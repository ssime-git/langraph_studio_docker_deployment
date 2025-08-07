"""
Orchestrator-Worker example: orchestrator splits, workers execute, aggregator combines.
Chat-compatible: messages state with add_messages; final assistant message appended.
"""
from typing import TypedDict, Annotated, Sequence, List, NotRequired
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langchain_openai import ChatOpenAI
from langchain_core.messages import AnyMessage, AIMessage, HumanMessage

llm = ChatOpenAI(model="gpt-4o-mini")


class State(TypedDict):
    messages: Annotated[Sequence[AnyMessage], add_messages]
    task: NotRequired[str]
    subtasks: NotRequired[List[str]]
    results: NotRequired[List[str]]
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
    subs = subs[:3] if subs else [task]
    return {"subtasks": subs}


def worker_factory(idx: int):
    def _worker(state: State):
        sub = state["subtasks"][idx]
        msg = llm.invoke(f"Do this subtask succinctly: {sub}")
        res = list(state.get("results", []))
        while len(res) <= idx:
            res.append("")
        res[idx] = msg.content
        return {"results": res}
    return _worker


def aggregate(state: State):
    parts = state.get("results", [])
    combined = "\n\n".join(f"- {p}" for p in parts if p)
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
