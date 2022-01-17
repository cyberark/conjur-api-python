import asyncio
from unittest import TestCase
from conjur_api.utils.decorators import allow_sync_invocation


@allow_sync_invocation()
class Container:
    def __init__(self, async_mode):
        self.async_mode = async_mode

    async def async_func(self):
        await asyncio.sleep(0.0001)
        return "Run successfully"


class AllowSyncModeDecoratorTest(TestCase):

    def test_sync_function_not_decorated(self):
        c = Container(False)
        self.assertEqual("Run successfully", c.async_func())

    def test_async_function_decoration(self):
        c = Container(True)
        self.assertEqual("Run successfully", asyncio.run(c.async_func()))
