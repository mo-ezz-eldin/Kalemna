from collections.abc import Callable
from typing import Any

from langchain.chat_models import ChatOpenAI

from src.domain.interfaces.ILlm import ILlm


class LocalLlm(ILlm):
    def __init__(self , temperature: float  , url : str , secret: str | None):

        self.llm = ChatOpenAI(temperature=temperature , base_url=url , api_key=secret ,model='kalemna_llm_assistant')
    async def generate(self, prompt: Any, parser: Any, details: dict, config: dict, guardrails: Callable | None = None):
        if guardrails is None:
            chain = prompt | self.llm | parser
        else:
            chain = prompt | self.llm | guardrails | parser

        response = await chain.ainvoke(details, config=config)

        return response


    async def execute_tools(self, prompt: Any, tools_list: list, details: dict, config: dict):
        llm_with_tools = self.llm.bind_tools(tools_list)

        chain = prompt | llm_with_tools

        response = await chain.ainvoke(details, config=config)

        return response

