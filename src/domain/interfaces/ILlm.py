from abc import ABC, abstractmethod
from typing import List, Any, Dict, Callable


class ILlm(ABC):
    @abstractmethod
    async def generate(self ,prompt : Any ,  parser : Any ,details : Dict ,config : Dict , guardrails: Callable | None = None ):
        pass

    @abstractmethod
    async def execute_tools(self ,  prompt : Any , tools_list : List , details : Dict , config : Dict) :
        pass