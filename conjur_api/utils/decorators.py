import logging
import inspect
import asyncio
from conjur_api.errors.errors import SyncInvocationInsideEventLoopError


def allow_sync_invocation():
    def allow_sync_mode(f):
        def wrapper(self, *args):
            should_run_async = getattr(self, "async_mode")
            if should_run_async:  # Function should remain async
                return f(self, *args)
            if asyncio.get_event_loop() is not None:
                logging.error(
                    f"Failed to run conjur_api {f.__name__} function in sync mode "
                    f"because code is running inside event loop")
                raise SyncInvocationInsideEventLoopError()
            return asyncio.run(f(self, *args))

        return wrapper

    def decorate(cls):
        for name, func in inspect.getmembers(cls, inspect.iscoroutinefunction):
            setattr(cls, name, allow_sync_mode(func))
        return cls

    return decorate
