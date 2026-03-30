"""
pytest configuration for the marcus_grant.dotfiles collection.

Injects the ansible_collections.marcus_grant.dotfiles namespace into sys.modules
so that unit tests can import collection modules directly without a full
ansible-test environment.
"""
import sys
import types
from pathlib import Path

_root = Path(__file__).parent


def _ensure_namespace(name: str, path=None):
    if name not in sys.modules:
        mod = types.ModuleType(name)
        mod.__path__ = [str(path)] if path else []
        mod.__package__ = name
        sys.modules[name] = mod
    return sys.modules[name]


_ensure_namespace('ansible_collections')
_ensure_namespace('ansible_collections.marcus_grant')
_dotfiles = _ensure_namespace('ansible_collections.marcus_grant.dotfiles', _root)
