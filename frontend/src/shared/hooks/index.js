"""
Shared Hooks Module
Re-exports existing hooks from their current location for easier imports
"""
# Re-export from original locations
from backend.hooks.useAuth import useAuth
from backend.hooks.useMediaQuery import useMediaQuery

# This allows imports like:
# from shared.hooks import useAuth, useMediaQuery

__all__ = ['useAuth', 'useMediaQuery']
