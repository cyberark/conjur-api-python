import asyncio
from unittest import TestCase
from conjur_api.utils.decorators import decorate_class_async_methods


class DecorateClassAsyncMethodsTest(TestCase):

    def test_class_decoration(self):
        def decorator(func):
            def wrapper(*args):
                return "decorated"

            return wrapper

        @decorate_class_async_methods(decorator)
        class Container:

            def func(self):
                return "not decorated"

            async def should_be_decorated(self):
                await asyncio.sleep(0.0001)
                return "not decorated"

        c = Container()
        self.assertEqual("not decorated", c.func())  # test sync functions are not decorated
        self.assertEqual("decorated", c.should_be_decorated())  # test async functions are decorated
