from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode

from src.application.graphs.state import Customer_State
from src.application.orchestrator import ChatOrchestrator
from src.application.decision_maker import DecisionMaker
from src.infrastructure.ai_models.intent_model import IntentModel
from src.infrastructure.ai_models.sentiment_model import SentimentClassifier

# استدعاء النودز اللي إنت بعتها فوق (افترض إنك حاططهم في ملف nodes.py)
from src.application.graphs.nodes import (
    Intent_Sentiment_Node,
    judge_and_extract_entities,
    decide_excute,
    finalize_node
)

# استدعاء الراوترات
from src.application.graphs.routes import route_whether_to_final_or_tools, route_after_decide

# استدعاء التوول
from src.application.graphs.tools import read_from_db


def build_customer_support_graph(orchestrator:ChatOrchestrator, decision_maker:DecisionMaker):
    workflow = StateGraph(Customer_State)

    # 2. أخذ نسخة من النودز (Classes Instantiation)
    intent_node = Intent_Sentiment_Node(orchestrator=orchestrator)
    judge_node = judge_and_extract_entities(decision_maker=decision_maker)
    decide_node = decide_excute()
    final_node = finalize_node()  # إنت حاطط الـ 'llm' جواها ستاتيك فمش هنباصي حاجة

    # نود التوولز
    tools_node = ToolNode([read_from_db])

    # 3. إضافة النودز للجراف
    workflow.add_node("intent_sentiment", intent_node)
    workflow.add_node("judge", judge_node)
    workflow.add_node("decide", decide_node)
    workflow.add_node("tools", tools_node)
    workflow.add_node("finalize", final_node)

    # 4. توصيل المسارات (Edges & Routing)

    # Entry Point (أول نود بتشتغل)
    workflow.set_entry_point("intent_sentiment")

    # من الموديلات السريعة للـ Judge
    workflow.add_edge("intent_sentiment", "judge")

    # من الـ Judge الراوتر الأول هيشتغل ويقرر يروح فين
    workflow.add_conditional_edges(
        "judge",
        route_whether_to_final_or_tools,
        {
            "decide": "decide",
            "finalize": "finalize"
        }
    )

    # من الـ Decide الراوتر التاني هيشتغل عشان يشوف الموديل طلب توول ولا لأ
    workflow.add_conditional_edges(
        "decide",
        route_after_decide,
        {
            "tools": "tools",
            "finalize": "finalize"
        }
    )

    # بعد ما التوول تخلص شغل وتجيب داتا، ترجع تاني للـ decide عشان الموديل يصيغ الرد
    workflow.add_edge("tools", "decide")

    # نود الـ finalize هي المحطة الأخيرة وبتنهي الجراف
    workflow.add_edge("finalize", END)

    # 5. تجميع الجراف
    app = workflow.compile()

    return app
