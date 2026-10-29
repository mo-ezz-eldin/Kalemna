from abc import ABC, abstractmethod
from collections.abc import Callable
from typing import Any


class ILlm(ABC):
    @abstractmethod
    async def generate(self, prompt: Any, parser: Any, details: dict, config: dict, guardrails: Callable | None = None):
        pass

    @abstractmethod
    async def execute_tools(self, prompt: Any, tools_list: list, details: dict, config: dict):
        pass

    @abstractmethod
    async def generate_with_structured_output(self , prompt:Any ,schema:Any , parser: Any, details: dict, config: dict, guardrails: Callable | None = None):
        pass


    @abstractmethod
    async def serve_structured_output_based_on_model_type(self):
        pass
