from functools import wraps, lru_cache
from flask import request, abort


@lru_cache
def is_token_valid(token: str) -> bool:
    if len(token.strip()) == 0:
        return False
    with open('access_tokens.txt') as f:
        allowed_tokens = [t.strip() for t in f.readlines()]
        if token in allowed_tokens:
            return True
    return False


def token_required(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        token = request.headers.get("access-token", "")
        if not is_token_valid(token):
            abort(404)
        return f(*args, **kwargs)
    return wrap
