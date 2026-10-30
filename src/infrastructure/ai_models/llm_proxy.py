from collections.abc import Callable
from typing import Any

from loguru import logger
from tenacity import AsyncRetrying, stop_after_attempt, wait_exponential

from src.domain.interfaces.ILlm import ILlm
from src.infrastructure.ai_models.Llm_factory import LLMHub


class LLMProxy(ILlm):
    def __init__(
        self,
        primary_provider: str,
        url : str,
        fallback_provider: str,
        fallback2_provider: str,
        fallback2_api_key: str,
        fallback_api_key: str,
        temperature: float,
    ):
        self.url = url
        self.fallback_provider = fallback_provider
        self.fallback_api_key = fallback_api_key
        self.fallback2_api_key = fallback2_api_key
        self.fallback2_provider = fallback2_provider
        self.temperature = temperature

        self.current_llm = LLMHub.create_object(primary_provider, secret='kalemna_llm_assistant', temperature = temperature ,  url = self.url)

        self.providers_chain = [
            {"name": primary_provider, "api_key": "kalemna_llm_assistant", "url": url},
            {"name": fallback_provider, "api_key": fallback_api_key, "url": None},
            {"name": fallback2_provider, "api_key": fallback2_api_key, "url": None},
        ]


        self.circuit_breaker = {
            primary_provider: 0,
            fallback_provider: 0,
            fallback2_provider: 0
        }

        self.cooldown_seconds = 240

    async def _execute_with_fallback(self, method_name: str, **kwargs):

        for provider_config in self.providers_chain:
            provider_name = provider_config["name"]

            # لو الوقت الحالي أصغر من وقت السماح، معناه إن الموديل ده واقع (Open)
            if time.time() < self.circuit_breaker[provider_name]:
                logger.warning(f"Circuit Breaker is OPEN for {provider_name}. Skipping to next provider...")
                continue


            try:

                llm_instance = LLMHub.create_object(
                    provider_name,
                    secret=provider_config["api_key"],
                    temperature=self.temperature,
                    url=provider_config["url"]
                )

                is_half_open = self.circuit_breaker[provider_name] != 0

                num_of_retries = 1 if is_half_open else 3

                async for attempt in AsyncRetrying(stop=stop_after_attempt(num_of_retries), wait=wait_exponential(multiplier=2)):
                    with attempt:
                        logger.info(f"Executing {method_name} using {provider_name}...")

                        method = getattr(llm_instance, method_name)

                        response =  await method(**kwargs)

                        if is_half_open:

                            logger.success(f"{provider_name} is BACK ONLINE! Closing Circuit Breaker.")

                            self.circuit_breaker[provider_name] = 0.0

                        return response




            except Exception as e:

                logger.error(f"{provider_name} failed all attempts due to: {e}. Opening Circuit Breaker!")

                self.circuit_breaker[provider_name] = time.time() + self.cooldown_seconds

                continue

        logger.critical("Disaster! ALL LLM Providers in the chain failed or are currently OPEN.")
        raise RuntimeError("All LLM Providers failed. Trigger Human Handoff or Safe Default.")

    async def generate(self , prompt:Any ,schema:Any , parser: Any, details: dict, config: dict, guardrails: Callable | None = None):
        return await self._execute_with_fallback(method_name='generate' ,
                                                 prompt=prompt ,
                                                 schema =schema ,
                                                 parser = parser ,
                                                 details=details,
                                                 config=config,
                                                 guardrails=guardrails)

    async def execute_tools(self, prompt: Any, tools_list: list, details: dict, config: dict):
        try:
            async for attempt in AsyncRetrying(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=2)):
                with attempt:
                    return await self.current_llm.execute_tools(
                        prompt=prompt, tools_list=tools_list, details=details, config=config
                    )

        except Exception as e:
            logger.error(
                f"loading fallback LLM : {self.fallback_provider} there is an error happened in primary LLM due to {e}"
            )

            try:
                self.current_llm = LLMHub.create_object(self.fallback_provider, self.fallback_api_key, self.temperature , url =None)
                async for attempt in AsyncRetrying(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=2)):
                    with attempt:
                        return await self.current_llm.execute_tools(
                    prompt=prompt, tools_list=tools_list, details=details, config=config
                    )

            except Exception as se_error:
                logger.error(
                    f"loading fallback LLM : {self.fallback2_provider} there is an error happened in our first fallback LLM due to {se_error}"
                )

            try:
                    self.current_llm = LLMHub.create_object(self.fallback2_provider, self.fallback2_api_key,
                                                            self.temperature, url = None)
                    async for attempt in AsyncRetrying(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=2)):
                        with attempt:
                            return await self.current_llm.execute_tools(
                                prompt=prompt, tools_list=tools_list, details=details, config=config
                            )

            except Exception as final_error:

                logger.critical(f"disaster error in fallback LLM due to {final_error}")
                raise RuntimeError("All LLM Providers failed during tool execution.")
