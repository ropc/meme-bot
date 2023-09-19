import abc
from typing import Dict, Optional
from pydantic import BaseModel

USER_INPUT_KEY = 'user_input'


class AbstractInput(BaseModel, abc.ABC):
    @abc.abstractmethod
    def get_input(self, context: Dict) -> Optional[str]:
        pass


class RawInput(AbstractInput):
    text: str

    def get_input(self, context: Dict) -> str:
        return self.text


class UserInput(AbstractInput):
    def get_input(self, context: Dict) -> Optional[str]:
        return context.get(USER_INPUT_KEY)


class ContextInput(AbstractInput):
    key: str
    prefix: Optional[str] = None
    suffix: Optional[str] = None

    def get_input(self, context: Dict) -> Optional[str]:
        text = context.get(self.key)
        if not text:
            return None
        prefix = self.prefix or ''
        suffix = self.suffix or ''
        return prefix + text + suffix
