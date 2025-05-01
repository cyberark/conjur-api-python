"""
Decorators module

This module holds all the decorators of the SDK
"""
import logging
import inspect
import asyncio
from conjur_api.errors.errors import SyncInvocationInsideEventLoopError

logger = logging.getLogger(__name__)

def allow_sync_invocation():
    """
    A class decorator, used to make all public async methods of the class to be invoke synchronically
    This action would take place only if the class has async_mode=False attribute
    """

    def allow_sync_mode(func):
        def wrapper(self, *args):
            should_run_async = getattr(self, "async_mode")
            should_run_async |= func.__name__.startswith("_")  # omit private functions
            if should_run_async:  # Function should remain async
                return func(self, *args)
            loop = _get_event_loop()
            if loop is not None and loop.is_running():
                logger.error(
                    "Failed to run conjur_api %s function in sync mode "
                    "because code is running inside event loop", func.__name__)
                raise SyncInvocationInsideEventLoopError()
            return asyncio.run(func(self, *args))

        return wrapper

    def decorate(cls):
        for name, func in inspect.getmembers(cls, inspect.iscoroutinefunction):
            setattr(cls, name, allow_sync_mode(func))
        return cls

    return decorate


def _get_event_loop():
    try:
        return asyncio.get_event_loop()
    except RuntimeError:  # No loop exist
        return None
    except Exception as err:
        logger.error("Couldn't get event loop for unknown reason. details: %s", err)
        raise
