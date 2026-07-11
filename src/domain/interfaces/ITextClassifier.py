from abc import ABC, abstractmethod
class ITextClassifier(ABC):
    @abstractmethod
    def predict(self,text)->dict:
        pass
