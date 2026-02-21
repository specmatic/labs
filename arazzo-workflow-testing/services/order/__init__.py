from typing import Annotated

from fastapi import Depends, FastAPI, HTTPException
from fastapi.concurrency import asynccontextmanager
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import ValidationError
from sqlmodel import Session

from common.database import Database
from order.event_bus import EventBus, EventType
from order.events import setup_event_handlers


def get_session():
    with Session(Database().engine) as session:
        yield session


def get_event_bus() -> EventBus:
    return EventBus()


@asynccontextmanager
async def lifespan(app: FastAPI):
    event_bus = EventBus()
    event_bus.start_consumer(EventType.ORDER_CREATED)
    event_bus.start_consumer(EventType.ORDER_DELIVERY)
    setup_event_handlers(event_bus)

    yield

    event_bus.stop()


SessionDep = Annotated[Session, Depends(get_session)]
KafkaDep = Annotated[EventBus, Depends(get_event_bus)]
app = FastAPI(lifespan=lifespan)
app.add_middleware(
    CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"]
)


@app.exception_handler(ValidationError)
@app.exception_handler(RequestValidationError)
def handle_validation_error(_, e: "RequestValidationError|ValidationError"):
    return JSONResponse(
        status_code=400,
        content={
            "error": "Bad Request",
            "message": str(e),
        },
    )


@app.exception_handler(HTTPException)
def http_error_handler(_, e: "HTTPException"):
    return JSONResponse(
        status_code=e.status_code,
        content={
            "error": e.__class__.__name__,
            "message": e.detail,
        },
    )


from order.routes import order_routes  # noqa: E402

app.include_router(order_routes)
