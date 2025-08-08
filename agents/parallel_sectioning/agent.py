"""
Parallelization - Sectioning example
Generates a joke, story, and poem in parallel, then aggregates them.
Exports: app (CompiledGraph)
"""
from typing import TypedDict, Annotated, Sequence, NotRequired
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langchain_openai import ChatOpenAI
from langchain_core.messages import AnyMessage, AIMessage, HumanMessage


# Configure LLM (relies on OPENAI_API_KEY in environment)
llm = ChatOpenAI(model="gpt-4o-mini")


class State(TypedDict):
    messages: Annotated[Sequence[AnyMessage], add_messages]
    topic: NotRequired[str]
    joke: NotRequired[str]
    story: NotRequired[str]
    poem: NotRequired[str]
    combined_output: NotRequired[str]


def _last_user_text(state: State) -> str:
    for m in reversed(state.get("messages", [])):
        if isinstance(m, HumanMessage) or getattr(m, "type", None) == "human":
            return m.content if isinstance(m.content, str) else str(m.content)
    return state.get("topic", "")


def call_llm_1(state: State):
    topic = state.get("topic") or _last_user_text(state)
    msg = llm.invoke(f"Write a short funny joke about {topic}.")
    return {"joke": msg.content}


def call_llm_2(state: State):
    topic = state.get("topic") or _last_user_text(state)
    msg = llm.invoke(f"Write a short bedtime story about {topic}.")
    return {"story": msg.content}


def call_llm_3(state: State):
    topic = state.get("topic") or _last_user_text(state)
    msg = llm.invoke(f"Write a short poem about {topic}.")
    return {"poem": msg.content}


def aggregator(state: State):
    topic = state.get("topic") or _last_user_text(state)
    story = state.get("story")
    joke = state.get("joke")
    poem = state.get("poem")

    parts = []
    if story:
        parts.append(f"STORY:\n{story}")
    if joke:
        parts.append(f"JOKE:\n{joke}")
    if poem:
        parts.append(f"POEM:\n{poem}")

    header = f"Here is a story, joke, and poem about {topic}!" if topic else "Collected pieces:"
    combined = header + ("\n\n" + "\n\n".join(parts) if parts else "\n(Waiting for sections...)" )

    # Only emit final assistant message when all sections are present
    done = all([story, joke, poem])
    if done:
        return {"combined_output": combined, "messages": [AIMessage(content=combined)]}
    else:
        return {"combined_output": combined}


# Build graph
_builder = StateGraph(State)
_builder.add_node("call_llm_1", call_llm_1)
_builder.add_node("call_llm_2", call_llm_2)
_builder.add_node("call_llm_3", call_llm_3)
_builder.add_node("aggregator", aggregator)

# parallel fan-out from START
_builder.add_edge(START, "call_llm_1")
_builder.add_edge(START, "call_llm_2")
_builder.add_edge(START, "call_llm_3")

# join in aggregator
_builder.add_edge("call_llm_1", "aggregator")
_builder.add_edge("call_llm_2", "aggregator")
_builder.add_edge("call_llm_3", "aggregator")
_builder.add_edge("aggregator", END)

app = _builder.compile()
