"""
Evaluator-Optimizer example: generate -> evaluate -> refine (single pass).
Chat-compatible: messages state with add_messages; final assistant message appended.
"""
from typing import TypedDict, Annotated, Sequence, NotRequired
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langchain_openai import ChatOpenAI
from langchain_core.messages import AnyMessage, AIMessage, HumanMessage

llm = ChatOpenAI(model="gpt-4o-mini")


class State(TypedDict):
    messages: Annotated[Sequence[AnyMessage], add_messages]
    prompt: NotRequired[str]
    draft: NotRequired[str]
    critique: NotRequired[str]
    improved: NotRequired[str]


def _last_user_text(state: State) -> str:
    for m in reversed(state.get("messages", [])):
        if isinstance(m, HumanMessage) or getattr(m, "type", None) == "human":
            return m.content if isinstance(m.content, str) else str(m.content)
    return state.get("prompt", "")


def generate(state: State):
    prompt = state.get("prompt") or _last_user_text(state)
    msg = llm.invoke(f"Write an initial response for: {prompt}")
    return {"draft": msg.content}


def evaluate(state: State):
    msg = llm.invoke(
        "Provide a brief, constructive critique (3 bullets max) of this text:\n"
        + state["draft"]
    )
    return {"critique": msg.content}


def refine(state: State):
    msg = llm.invoke(
        "Improve the original text using the critique. Return the improved version only.\n"
        f"CRITIQUE:\n{state['critique']}\n\nORIGINAL:\n{state['draft']}"
    )
    return {"improved": msg.content, "messages": [AIMessage(content=msg.content)]}


_builder = StateGraph(State)
_builder.add_node("generate", generate)
_builder.add_node("evaluate", evaluate)
_builder.add_node("refine", refine)

_builder.add_edge(START, "generate")
_builder.add_edge("generate", "evaluate")
_builder.add_edge("evaluate", "refine")
_builder.add_edge("refine", END)

app = _builder.compile()
