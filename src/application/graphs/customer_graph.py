from langgraph.graph import StateGraph, END,START
from langgraph.prebuilt import ToolNode
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from src.domain.interfaces.IDatabase import IDatabase

from src.application.graphs.state import Customer_State
from src.application.orchestrator import ChatOrchestrator
from src.application.decision_maker import DecisionMaker


from src.application.graphs.nodes import (
    Intent_Sentiment_Node,
    judge_and_extract_entities,
    decide_excute,
    finalize_node
)

#llm | tools (read_from_db completion)
from src.application.graphs.routes import route_whether_to_final_or_tools, route_after_decide


from src.application.graphs.tools import read_from_db


def build_customer_support_graph(orchestrator:ChatOrchestrator,
                                 decision_maker:DecisionMaker,
                                 db :IDatabase,
                                 chckpointer : AsyncPostgresSaver):
    workflow = StateGraph(Customer_State)


    intent_node = Intent_Sentiment_Node(orchestrator=orchestrator)
    judge_node = judge_and_extract_entities(decision_maker=decision_maker)
    decide_node = decide_excute()
    final_node = finalize_node()

    tools_node = ToolNode([read_from_db])

    workflow.add_node("intent_sentiment", intent_node)
    workflow.add_node("judge", judge_node)
    workflow.add_node("decide", decide_node)
    workflow.add_node("tools", tools_node)
    workflow.add_node("finalize", final_node)


    workflow.add_edge(START, 'intent_sentiment')

    workflow.add_edge("intent_sentiment", "judge")


    workflow.add_conditional_edges(
        "judge",
        route_whether_to_final_or_tools,
        {
            "decide": "decide",
            "finalize": "finalize"
        }
    )

    workflow.add_conditional_edges(
        "decide",
        route_after_decide,
        {
            "tools": "tools",
            "finalize": "finalize"
        }
    )

    workflow.add_edge("tools", "decide")

    workflow.add_edge("finalize", END)


    app = workflow.compile(checkpointer=chckpointer)

    return app
