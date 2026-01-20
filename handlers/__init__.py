from .servers import router as servers_router
from .stats import router as stats_router
from .hosting import router as hosting_router

__all__ = ["servers_router", "stats_router", "hosting_router"]
