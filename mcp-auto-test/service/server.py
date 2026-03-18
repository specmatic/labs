import contextlib
from typing import Literal

from mcp.server.fastmcp import FastMCP
from starlette.applications import Starlette
from starlette.responses import JSONResponse
from starlette.routing import Mount, Route

from order_service import create_return_quote as create_return_quote_impl
from order_service import get_order_summary as get_order_summary_impl

mcp = FastMCP("Order Tools Lab", host="0.0.0.0", json_response=True)


@mcp.tool()
def get_order_summary(order_id: str, include_history: bool = False) -> dict:
    """Return a summary for a known order."""
    return get_order_summary_impl(order_id=order_id, include_history=include_history)


@mcp.tool()
def create_return_quote(
    order_id: str,
    reason: Literal["damaged", "no_longer_needed"],
    opened: bool,
    days_since_delivery: int,
) -> dict:
    """Create a return quote for an order."""
    return create_return_quote_impl(
        order_id=order_id,
        reason=reason,
        opened=opened,
        days_since_delivery=days_since_delivery,
    )


async def health(_request):
    return JSONResponse({"status": "ok"})


@contextlib.asynccontextmanager
async def lifespan(_app: Starlette):
    async with mcp.session_manager.run():
        yield


app = Starlette(
    routes=[
        Route("/health", endpoint=health),
        Mount("/", app=mcp.streamable_http_app()),
    ],
    lifespan=lifespan,
)
