from collections.abc import Callable
from typing import Any

from langchain_openai import ChatOpenAI
from loguru import logger

from src.domain.interfaces.ILlm import ILlm


class LocalLlm(ILlm):
    def __init__(self , temperature: float  , url : str , secret: str | None):

        self.llm = ChatOpenAI(temperature=temperature , base_url='https://'+ url +'/v1' , api_key=secret ,model='kalemna_llm_assistant')

    async def generate(self, prompt: Any, schema: Any, parser: Any, details: dict, config: dict, guardrails: Callable | None = None):
        if guardrails is None: # finalize node
            chain = prompt | self.llm | parser

        else: # structure - output
            if hasattr(schema, 'model_json_schema'):
                json_schema = schema.model_json_schema()
                schema_name = schema.__name__
            else:
                json_schema = schema
                schema_name = json_schema.get("title", "structured_output")

            # Use vLLM-compatible response_format with json_schema type
            # and pass extra vLLM options (like disable thinking) via extra_body
            structured_llm = self.llm.bind(
                response_format={
                    "type": "json_schema",
                    "json_schema": {
                        "name": schema_name,
                        "schema": json_schema,
                    },
                },
                extra_body={
                    "chat_template_kwargs": {
                        "enable_thinking": False,
                    }
                },
            )


            chain = prompt | structured_llm | guardrails | parser

        response = await chain.ainvoke(details, config=config)

        logger.debug(f'response: {response}')

        return response



    async def execute_tools(self, prompt: Any, tools_list: list, details: dict, config: dict):
        llm_with_tools = self.llm.bind_tools(tools_list)

        logger.debug(f'llm_with_tools bound with vLLM json_schema format : {llm_with_tools}')

        chain = prompt | llm_with_tools



        response = await chain.ainvoke(details, config=config)

        return response


