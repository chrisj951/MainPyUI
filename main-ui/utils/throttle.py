import time
from functools import wraps
from typing import Any, Callable, Protocol, cast


class _ForceRefreshable(Protocol):
    _force_refresh: bool
    def force_refresh(self) -> None: ...

def limit_refresh(seconds: float = 15.0):
    def decorator(func: Callable[..., Any]) -> Any:

        # Detect classmethod and unwrap
        is_classmethod = isinstance(func, classmethod)
        if is_classmethod:
            orig_func = func.__func__
        else:
            orig_func = func

        last_called = [0.0]
        last_result = [None]

        @wraps(orig_func)
        def wrapper(*args, **kwargs):
            now = time.time()
            if now - last_called[0] >= seconds or getattr(wrapper, "_force_refresh", False):
                last_called[0] = now
                last_result[0] = orig_func(*args, **kwargs)
                wrapper_typed._force_refresh = False
            return last_result[0]

        wrapper_typed = cast(_ForceRefreshable, wrapper)
        wrapper_typed._force_refresh = False

        # Add method to force refresh
        def force():
            wrapper_typed._force_refresh = True

        wrapper_typed.force_refresh = force

        # If it was a classmethod, return it wrapped back as classmethod
        if is_classmethod:
            return classmethod(wrapper)

        return wrapper

    return decorator
