from langgraph.graph import StateGraph, START, END

from .state import AgentState
from .router import route_query


def sql_node(state):
    # call your SQL agent here
    ...
    

def build_graph():

    graph = StateGraph(AgentState)

    graph.add_node("router", route_query)
    graph.add_node("sql_agent", sql_node)

    graph.add_edge(START, "router")
    graph.add_edge("router", "sql_agent")
    graph.add_edge("sql_agent", END)

    return graph.compile()