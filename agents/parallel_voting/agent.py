"""
Parallelization - Voting example
Runs the same task multiple times in parallel and chooses the best result.
Exports: app (CompiledGraph)
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
    draft1: NotRequired[str]
    draft2: NotRequired[str]
    draft3: NotRequired[str]
    best: NotRequired[str]


def _last_user_text(state: State) -> str:
    for m in reversed(state.get("messages", [])):
        if isinstance(m, HumanMessage) or getattr(m, "type", None) == "human":
            return m.content if isinstance(m.content, str) else str(m.content)
    return state.get("topic", "")


def write_variant(prompt: str):
    def _node(state: State):
        msg = llm.invoke(prompt.format(topic=state["topic"]))
        return {"text": msg.content}
    return _node


def variant1(state: State):
    topic = state.get("topic") or _last_user_text(state)
    msg = llm.invoke(f"Write a short product tagline about {topic} with humor.")
    return {"draft1": msg.content}


def variant2(state: State):
    topic = state.get("topic") or _last_user_text(state)
    msg = llm.invoke(f"Write a concise, professional product tagline about {topic}.")
    return {"draft2": msg.content}


def variant3(state: State):
    topic = state.get("topic") or _last_user_text(state)
    msg = llm.invoke(f"Write an edgy, bold product tagline about {topic}.")
    return {"draft3": msg.content}


def choose_best(state: State):
    # Use the LLM to pick best among options
    instruction = (
        "You are selecting the best tagline. Consider clarity, memorability, and appeal.\n"
        f"Option A: {state['draft1']}\n"
        f"Option B: {state['draft2']}\n"
        f"Option C: {state['draft3']}\n"
        "Respond with the chosen option letter and the final improved tagline."
    )
    msg = llm.invoke(instruction)
    return {"best": msg.content, "messages": [AIMessage(content=msg.content)]}


_builder = StateGraph(State)
_builder.add_node("variant1", variant1)
_builder.add_node("variant2", variant2)
_builder.add_node("variant3", variant3)
_builder.add_node("choose_best", choose_best)

_builder.add_edge(START, "variant1")
_builder.add_edge(START, "variant2")
_builder.add_edge(START, "variant3")
_builder.add_edge("variant1", "choose_best")
_builder.add_edge("variant2", "choose_best")
_builder.add_edge("variant3", "choose_best")
_builder.add_edge("choose_best", END)

app = _builder.compile()
