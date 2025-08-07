"""
Routing example: route to specialist based on topic, then respond.
Chat-compatible: messages state with add_messages; final assistant response appended.
"""
from typing import TypedDict, Annotated, Sequence, Literal, NotRequired
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langchain_openai import ChatOpenAI
from langchain_core.messages import AnyMessage, AIMessage, HumanMessage

llm = ChatOpenAI(model="gpt-4o-mini")


class State(TypedDict):
    messages: Annotated[Sequence[AnyMessage], add_messages]
    topic: NotRequired[str]
    route: NotRequired[Literal["tech", "health", "finance"]]
    answer: NotRequired[str]


def _last_user_text(state: State) -> str:
    for m in reversed(state.get("messages", [])):
        if isinstance(m, HumanMessage) or getattr(m, "type", None) == "human":
            return m.content if isinstance(m.content, str) else str(m.content)
    return state.get("topic", "")


def router(state: State):
    topic = state.get("topic") or _last_user_text(state)
    prompt = (
        "Classify the user's request into one of: tech, health, finance.\n"
        f"Request: {topic}\nOnly output the single label."
    )
    msg = llm.invoke(prompt)
    label = msg.content.strip().lower()
    if label not in {"tech", "health", "finance"}:
        label = "tech"
    return {"route": label}


def tech_specialist(state: State):
    topic = state.get("topic") or _last_user_text(state)
    msg = llm.invoke(f"As a software expert, answer: {topic}")
    return {"answer": msg.content}


def health_specialist(state: State):
    topic = state.get("topic") or _last_user_text(state)
    msg = llm.invoke(f"As a medical writer (not medical advice), answer: {topic}")
    return {"answer": msg.content}


def finance_specialist(state: State):
    topic = state.get("topic") or _last_user_text(state)
    msg = llm.invoke(f"As a finance analyst (not financial advice), answer: {topic}")
    return {"answer": msg.content}


def respond(state: State):
    return {"messages": [AIMessage(content=state["answer"])]}


_builder = StateGraph(State)
_builder.add_node("router", router)
_builder.add_node("tech_specialist", tech_specialist)
_builder.add_node("health_specialist", health_specialist)
_builder.add_node("finance_specialist", finance_specialist)
_builder.add_node("respond", respond)

_builder.add_edge(START, "router")
# Conditional edges based on state["route"]
_builder.add_conditional_edges(
    "router",
    lambda s: s["route"],
    {
        "tech": "tech_specialist",
        "health": "health_specialist",
        "finance": "finance_specialist",
    },
)

_builder.add_edge("tech_specialist", "respond")
_builder.add_edge("health_specialist", "respond")
_builder.add_edge("finance_specialist", "respond")
_builder.add_edge("respond", END)

app = _builder.compile()
