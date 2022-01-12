import asyncio
from unittest import TestCase
from conjur_api.utils.decorators import  allow_sync_invocation


class AllowSyncModeDecoratorTest(TestCase):

    def test_sync_function_not_decorated(self):
        @allow_sync_invocation()
        class Container:
            def __init__(self):
                self.async_mode = False

            async def async_func(self):
                await asyncio.sleep(0.0001)
                return "Run successfully"

        c = Container()
        self.assertEqual("Run successfully", c.async_func())

    def test_async_function_decoration(self):
        @allow_sync_invocation()
        class Container:
            def __init__(self):
                self.async_mode = True

            async def async_func(self):
                await asyncio.sleep(0.0001)
                return "Run successfully"

        c = Container()
        self.assertEqual("Run successfully", asyncio.run(c.async_func()))
