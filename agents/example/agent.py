"""
Agent exemple minimal fonctionnel
"""
from typing import TypedDict, Annotated, Sequence
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
from langchain_core.messages import AnyMessage
from langchain_openai import ChatOpenAI


class State(TypedDict):
    messages: Annotated[Sequence[AnyMessage], add_messages]


def agent_node(state: State):
    """Nœud principal de l'agent"""
    llm = ChatOpenAI(model="gpt-3.5-turbo")
    response = llm.invoke(state["messages"])
    return {"messages": [response]}


# Construction du graphe
graph = StateGraph(State)
graph.add_node("agent", agent_node)
graph.set_entry_point("agent")
graph.add_edge("agent", END)

# Compilation - LangGraph Server attend un objet `app`
app = graph.compile()