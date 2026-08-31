from typing import Callable, Dict, Any, List
from loguru import logger
from tenacity import AsyncRetrying, stop_after_attempt, wait_exponential

from src.domain.interfaces.ILlm import ILlm
from src.infrastructure.ai_models.Llm_factory import LLMHub


class LLMProxy(ILlm):
    def __init__(self, primary_provider: str, fallback_provider: str,
                 primary_api_key: str, fallback_api_key: str, temperature: float):


        self.fallback_provider = fallback_provider
        self.fallback_api_key = fallback_api_key
        self.temperature = temperature


        self.current_llm = LLMHub.create_object(primary_provider, primary_api_key, temperature)

    async def generate(self, prompt: Any, parser: Any, details: Dict,config : Dict, guardrails: Callable | None = None ):
        try:
            async for attempt in AsyncRetrying(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=2)):
                with attempt:
                    return await self.current_llm.generate(prompt=prompt, guardrails=guardrails, parser=parser, details=details, config=config)

        except Exception as e:

            logger.error(
                f" loading fallback LLM : {self.fallback_provider} there is an error happened in primary LLM due to {e}")

            try:

                self.current_llm = LLMHub.create_object(self.fallback_provider, self.fallback_api_key, self.temperature)

                return await self.current_llm.generate(prompt=prompt, guardrails=guardrails, parser=parser, details=details, config=config)

            except Exception as fallback_error:

                logger.critical(f"disaster error in fallback LLM due to {fallback_error}")
                raise RuntimeError("All LLM Providers failed. Trigger Human Handoff or Safe Default.")

    async def execute_tools(self, prompt: Any, tools_list: List, details: Dict , config: Dict ):
        try:

            async for attempt in AsyncRetrying(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=2)):
                with attempt:
                    return await self.current_llm.execute_tools(prompt=prompt, tools_list=tools_list, details=details ,config=config)

        except Exception as e:
            logger.error(f"loading fallback LLM : {self.fallback_provider} there is an error happened in primary LLM due to {e}")

            try:
                self.current_llm = LLMHub.create_object(self.fallback_provider, self.fallback_api_key, self.temperature)
                return await self.current_llm.execute_tools(prompt=prompt, tools_list=tools_list, details=details ,config=config)

            except Exception as fallback_error:
                logger.critical(f"disaster error in fallback LLM due to {fallback_error}")
                raise RuntimeError("All LLM Providers failed during tool execution.")


