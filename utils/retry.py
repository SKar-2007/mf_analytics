import time
import functools
import logging
from typing import Callable, Optional, Type, Tuple

logger = logging.getLogger("bluestock.retry")


def retry(
    max_attempts: int = 3,
    delay: float = 2.0,
    backoff: float = 2.0,
    exceptions: Tuple[Type[Exception], ...] = (Exception,),
    on_retry: Optional[Callable] = None,
) -> Callable:
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            last_exc = None
            wait = delay
            for attempt in range(1, max_attempts + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exc = e
                    if attempt < max_attempts:
                        logger.warning(
                            "%s attempt %d/%d failed: %s. Retrying in %.1fs...",
                            func.__name__, attempt, max_attempts, e, wait,
                        )
                        if on_retry:
                            on_retry(attempt, e)
                        time.sleep(wait)
                        wait *= backoff
                    else:
                        logger.error(
                            "%s failed after %d attempts: %s",
                            func.__name__, max_attempts, e,
                        )
            raise last_exc  # type: ignore
        return wrapper
    return decorator


def rate_limiter(max_per_second: float = 2.0) -> Callable:
    import threading
    lock = threading.Lock()
    last_call: float = 0.0

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            nonlocal last_call
            with lock:
                elapsed = time.time() - last_call
                min_interval = 1.0 / max_per_second
                if elapsed < min_interval:
                    time.sleep(min_interval - elapsed)
                last_call = time.time()
            return func(*args, **kwargs)
        return wrapper
    return decorator
