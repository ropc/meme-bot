import abc
from typing import Dict, Union
from pydantic import BaseModel

USER_INPUT_KEY = 'user_input'


class AbstractInput(BaseModel, abc.ABC):
    @abc.abstractmethod
    def get_input(self, context: Dict) -> str:
        pass


class RawInput(AbstractInput):
    text: str

    def get_input(self, context: Dict) -> str:
        return self.text


class UserInput(AbstractInput):
    def get_input(self, context: Dict) -> str:
        return context[USER_INPUT_KEY]


class ContextInput(AbstractInput):
    key: str

    def get_input(self, context: Dict) -> str:
        return context[self.key]


PluginInput = Union[ContextInput, RawInput, UserInput]
