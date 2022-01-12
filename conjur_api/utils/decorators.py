import asyncio
import inspect


def allow_sync_mode(f):
    def wrapper(self, *args):
        if not getattr(self, "async_mode") and asyncio.iscoroutinefunction(f):
            return asyncio.run(f(self, *args))
        return f(self, *args)

    return wrapper


def decorate_class_async_methods(decorator):
    def decorate(cls):
        for name, attr in inspect.getmembers(cls,
                                             inspect.iscoroutinefunction):  # there's propably a better way to do this
            setattr(cls, name, decorator(getattr(cls, name)))
        return cls

    return decorate
