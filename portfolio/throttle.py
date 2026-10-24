"""
Per-visitor counters kept in Django's cache: the rate limits on the chat and
contact endpoints, and the admin sign-in lockout.

The cache is the default local-memory cache, which is per process; the site
runs one gunicorn process, so every request sees the same counters. Counters
reset when the process restarts, which is acceptable for abuse damping.
"""
from django.core.cache import cache


def client_ip(request):
    """
    The visitor's address, used only as a counter key and never stored.

    Cloudflare fronts the site and sends CF-Connecting-IP. Otherwise the
    right-most X-Forwarded-For entry is the one Render's proxy added; entries
    to its left can be written by the visitor.
    """
    cloudflare = request.META.get("HTTP_CF_CONNECTING_IP", "").strip()
    if cloudflare:
        return cloudflare
    hops = [hop.strip() for hop in request.META.get("HTTP_X_FORWARDED_FOR", "").split(",") if hop.strip()]
    if hops:
        return hops[-1]
    return request.META.get("REMOTE_ADDR") or "unknown"


def hit(key, window):
    """Count one event under `key` in a window of `window` seconds; return the new count."""
    cache.add(key, 0, timeout=window)
    try:
        return cache.incr(key)
    except ValueError:  # the key expired between add() and incr()
        cache.set(key, 1, timeout=window)
        return 1


def count(key):
    return cache.get(key) or 0


def reset(key):
    cache.delete(key)


def exceeded(namespace, ip, limits):
    """
    Count one request from `ip` against each (limit, window in seconds) pair;
    True once any of them is over its limit.
    """
    limited = False
    for limit, window in limits:
        if hit(f"{namespace}:rate:{window}:{ip}", window) > limit:
            limited = True
    return limited
