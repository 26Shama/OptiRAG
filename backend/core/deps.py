# backend/core/deps.py

def require_auth(*args, **kwargs):
    """
    Auth removed. All routes are now open-access.
    """
    return "guest_user"  # placeholder, returned value can still be used if route expects it
