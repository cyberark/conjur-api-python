import asyncio
from unittest import TestCase
from conjur_api.utils.decorators import allow_sync_mode


class AllowSyncModeDecoratorTest(TestCase):

    def test_sync_function_not_decorated(self):
        class Container:
            def __init__(self):
                self.async_mode = False

            @allow_sync_mode
            async def async_func(self):
                await asyncio.sleep(0.0001)
                return "Run successfully"

        c = Container()
        self.assertEqual("Run successfully", c.async_func())

    def test_async_function_decoration(self):
        class Container:
            def __init__(self):
                self.async_mode = True

            @allow_sync_mode
            async def async_func(self):
                await asyncio.sleep(0.0001)
                return "Run successfully"

        c = Container()
        self.assertEqual("Run successfully", asyncio.run(c.async_func()))
