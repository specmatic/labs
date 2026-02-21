from typing import Annotated

from fastapi import Depends, FastAPI, HTTPException
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import ValidationError
from sqlmodel import Session

from common.database import Database


def get_session():
    with Session(Database().engine) as session:
        yield session


SessionDep = Annotated[Session, Depends(get_session)]
app = FastAPI()
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


from warehouse.routes import warehouse_router  # noqa: E402

app.include_router(warehouse_router)
