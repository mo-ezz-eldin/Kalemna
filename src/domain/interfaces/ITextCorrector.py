from abc import ABC, abstractmethod
class ITextCorrector(ABC):
    @abstractmethod
    def predict(self,text)->str:
        pass