from abc import ABC, abstractmethod


class LLMProvider(ABC):

    @abstractmethod
    def chat(self, messages, tools=None):
        pass