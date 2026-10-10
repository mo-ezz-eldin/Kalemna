from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from langgraph.graph import END, START, StateGraph
from langgraph.prebuilt import ToolNode

from src.application.decision_maker import DecisionMaker
from src.application.graphs.Nodes import (
    Intent_Sentiment_Node,
    decide_excute,
    finalize_node,
    judge_and_extract_entities,
)
from src.application.graphs.routes import (
    route_after_decide,
    route_whether_to_final_or_tools,
)
from src.application.graphs.State import Customer_State
from src.application.graphs.tools import get_tools
from src.application.orchestrator import ChatOrchestrator
from src.domain.interfaces.IDatabase import IDatabase
from src.domain.interfaces.ILlm import ILlm


def build_customer_support_graph(
    orchestrator: ChatOrchestrator,
    decision_maker: DecisionMaker,
    db: IDatabase,
    chckpointer: AsyncPostgresSaver,
    llm_proxy: ILlm,
):
    workflow = StateGraph(Customer_State)

    my_tools = get_tools(db=db)

    intent_node = Intent_Sentiment_Node(orchestrator=orchestrator)
    judge_node = judge_and_extract_entities(decision_maker=decision_maker, llm_proxy=llm_proxy)

    decide_node = decide_excute(tools_list=my_tools, llm_proxy=llm_proxy)
    final_node = finalize_node(llm_proxy=llm_proxy)

    tools_node = ToolNode(my_tools)

    workflow.add_node("intent_sentiment", intent_node)
    workflow.add_node("judge", judge_node)
    workflow.add_node("decide", decide_node)
    workflow.add_node("tools", tools_node)
    workflow.add_node("finalize", final_node)

    workflow.add_edge(START, "intent_sentiment")
    workflow.add_edge("intent_sentiment", "judge")

    workflow.add_conditional_edges(
        "judge", route_whether_to_final_or_tools, {"decide": "decide", "finalize": "finalize"}
    )

    workflow.add_conditional_edges("decide", route_after_decide, {"tools": "tools", "finalize": "finalize"})

    workflow.add_edge("tools", "decide")
    workflow.add_edge("finalize", END)

    app = workflow.compile(checkpointer=chckpointer)

    return app
