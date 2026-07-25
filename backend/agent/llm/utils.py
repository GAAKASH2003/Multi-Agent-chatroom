import time
from functools import wraps

def with_delay(seconds: int = 2):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            result = func(*args, **kwargs)
            print(f"[delay] Waiting {seconds}s after {func.__name__}...")
            time.sleep(seconds)
            return result
        return wrapper
    return decorator