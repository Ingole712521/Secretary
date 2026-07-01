"""Port interfaces for infrastructure adapters and future services.

Protocols defined here follow the dependency inversion principle: application
code depends on these abstractions, not concrete implementations.
"""

from app.interfaces.protocols import (
    AIRouterServiceProtocol,
    MemoryServiceProtocol,
    ToolServiceProtocol,
)

__all__ = [
    "AIRouterServiceProtocol",
    "MemoryServiceProtocol",
    "ToolServiceProtocol",
]
