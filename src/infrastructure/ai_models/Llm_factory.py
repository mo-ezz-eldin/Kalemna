from src.domain.interfaces.ILlm import ILlm
from src.infrastructure.ai_models.Google_Llm import Google_Llm
from src.infrastructure.ai_models.Cohere_llm import Cohere_llm


class LLMHub:
    _registry = {'google_gemini': Google_Llm ,
                 'cohere' : Cohere_llm}

    @staticmethod
    def create_object(model_type: str, secret: str | None, temperature: float) -> ILlm:

        clean_provider = model_type.lower()

        llm_class = LLMHub._registry.get(model_type)

        if not llm_class:
            raise ValueError(f"Provider '{clean_provider}' is not supported in LLMHub.")


        return llm_class(temperature=temperature, secret=secret)
