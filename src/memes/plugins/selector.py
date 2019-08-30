import attr
from typing import Dict, Callable, Generic, TypeVar
from PIL import Image
from . import BasePlugin

A = TypeVar('A', bound=BasePlugin)
B = TypeVar('B', bound=BasePlugin)

@attr.s(kw_only=True)
class Selector(BasePlugin, Generic[A, B]):
    predicate: Callable[[Dict], bool] = attr.ib()
    plugin_a: A = attr.ib()
    plugin_b: B = attr.ib()

    async def run(self, image: Image, context: Dict):
        #pylint: disable=not-callable
        plugin = self.plugin_a if self.predicate(context) else self.plugin_b
        await plugin.run(image, context)


@attr.s(kw_only=True)
class StartsWithSelector(Selector):
    startswith: str = attr.ib()
    predicate: Callable[[Dict], bool] = attr.ib(default=attr.Factory(lambda self: self.inputstartswith(), takes_self=True))

    def inputstartswith(self):
        return lambda ctx: ctx[self.inputtextkey].startswith(self.startswith)
