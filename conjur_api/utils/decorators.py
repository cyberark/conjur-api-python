import logging
import inspect
import asyncio
from conjur_api.errors.errors import SyncInvocationInsideEventLoopError


def allow_sync_invocation():
    def allow_sync_mode(f):
        def wrapper(self, *args):
            should_run_async = getattr(self, "async_mode")
            should_run_async |= f.__name__.startswith("_")  # omit private functions
            if should_run_async:  # Function should remain async
                return f(self, *args)
            loop = _get_event_loop()
            if loop is not None and loop.is_running():
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


def _get_event_loop():
    try:
        return asyncio.get_event_loop()
    except RuntimeError:  # No loop exist
        return None
    except Exception as err:
        logging.error(f"Couldn't get event loop for unknown reason. details: {err}")
        raise
