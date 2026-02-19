from typing import Annotated

from fastapi import APIRouter, HTTPException, Query
from sqlmodel import select

from common.models import User
from location import SessionDep
from location.models import Location

location_router = APIRouter()


@location_router.get("/location", response_model=Location)
async def get_location(session: SessionDep, user_email: Annotated[str, Query(alias="userEmail", strict=True)]):
    statement = select(User).where(User.user_email == user_email)
    user = session.exec(statement).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return Location.model_validate({"userId": user.user_id, "locationCode": user.location_code})
