# lib/feature_flags.py
import os

def on(name: str, default: str = "false") -> bool:
    """
    Returns True if an environment variable (feature flag) is enabled.
    We store flags in Replit 'Secrets' so you can flip them without code changes.
    Example: FEATURE_COMPANY_INTENT_LIST=true
    """
    return os.getenv(name, default).strip().lower() == "true"
