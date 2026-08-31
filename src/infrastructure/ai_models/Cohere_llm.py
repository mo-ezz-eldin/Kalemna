from typing import Any, Dict, Callable, List
from langchain_cohere import ChatCohere
from src.domain.interfaces.ILlm import ILlm

class Cohere_llm(ILlm):

    def __init__(self  ,secret : str , temperature : float):
        self.llm = ChatCohere(model="command-r-plus-08-2024",
                                      cohere_api_key=secret,
                                      temperature=temperature)

    async def generate(self, prompt: Any, parser: Any, details: Dict,config :Dict , guardrails: Callable | None = None):
        if guardrails is None:
            chain = prompt | self.llm | parser
        else:
            chain = prompt | self.llm | guardrails | parser

        response = await chain.ainvoke(details , config=config)

        return response

    async def execute_tools(self, prompt: Any, tools_list: List, details: Dict ,config: Dict ):

        llm_with_tools = self.llm.bind_tools(tools_list)

        chain = prompt | llm_with_tools

        response = await chain.ainvoke(details,config=config)

        return response