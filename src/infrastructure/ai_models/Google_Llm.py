from typing import Any, List, Optional, Dict, Callable
from langchain_google_genai import ChatGoogleGenerativeAI
from src.domain.interfaces.ILlm import ILlm
from loguru import logger

class Google_Llm(ILlm):
    def __init__(self ,temperature : float , secret : str):
        self.llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash",
        google_api_key=secret,
        temperature=temperature)

    async def generate(self , prompt : Any    , parser : Any ,details : Dict , config : Dict , guardrails: Callable | None = None ) :
         if guardrails is None:
             chain = prompt | self.llm  | parser
         else:
             chain = prompt | self.llm | guardrails | parser


         response = await chain.ainvoke(details , config=config)

         return response

    async def execute_tools(self ,  prompt : Any , tools_list : List , details : Dict , config : dict) :

        llm_with_tools = self.llm.bind_tools(tools_list)

        chain = prompt | llm_with_tools

        response = await chain.ainvoke(details , config=config)


        return response
