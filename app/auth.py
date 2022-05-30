from functools import wraps, lru_cache
from flask import request, abort, current_app


@lru_cache
def is_token_valid(token: str) -> bool:
    if not token.strip():
        return False
    with open(current_app.config["ACCESS_TOKENS_FILENAME"]) as f:
        allowed_tokens = {t.strip() for t in f.readlines()}
    return token in allowed_tokens


def token_required(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        token = request.headers.get("access-token", "")
        if not is_token_valid(token):
            abort(404)
        return f(*args, **kwargs)
    return wrap
