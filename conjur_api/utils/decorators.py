import asyncio
import inspect


def allow_sync_invocation():
    def allow_sync_mode(f):
        def wrapper(self, *args):
            if not getattr(self, "async_mode"):
                return asyncio.run(f(self, *args))
            return f(self, *args)

        return wrapper

    def decorate(cls):
        for name, func in inspect.getmembers(cls, inspect.iscoroutinefunction):
            setattr(cls, name, allow_sync_mode(func))
        return cls

    return decorate
