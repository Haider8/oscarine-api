from fastapi import APIRouter, Depends, HTTPException
from fastapi.encoders import jsonable_encoder
from datetime import timedelta

from sqlalchemy.orm import Session
from app.api.utils.db import get_db
from app.models.owner import OwnerCreate, OwnerDetails
from app.crud.owner import create_owner, get_by_id
from app.api.utils.error import expected_integrity_error
from app.models.token import Token
from app.models.owner import OwnerLogin
from app.crud.owner import authenticate, update_owner_info
from app.core import config
from app.core.jwt import create_access_token
from app.models.owner import OwnerUpdate
from app.db_models.owner import Owner as DBOwnerModel
from app.api.utils.owner_security import get_current_owner


router = APIRouter()


@router.post("/owners", response_model=OwnerDetails)
async def register_owner(
        *,
        db: Session = Depends(get_db),
        data: OwnerCreate
):
    """registering new owners."""
    with expected_integrity_error(db, detail="There was a conflict with an existing user", debug=False):
        owner = create_owner(db, user_in=data)
    return owner


@router.get("/owners/{owner_id}", response_model=OwnerDetails)
async def owner_by_id(
    *,
    owner_id: int,
    db: Session = Depends(get_db)
):
    owner = get_by_id(db, owner_id=owner_id)
    if owner:
        return OwnerDetails(**jsonable_encoder(owner))
    raise HTTPException(
        status_code=404,
        detail="Can't find owner with that owner id"
    )


@router.post("/owner_login", response_model=Token, tags=["owner", "login"])
def owner_login_access_token(
        data: OwnerLogin,
        db: Session = Depends(get_db)
):
    """
    OAuth2 compatible token login for owners, get an access token for future requests
    """
    owner = authenticate(
        db, email=data.email, password=data.password
    )
    if not owner:
        raise HTTPException(
            status_code=400,
            detail="Incorrect email or password"
        )
    access_token_expires = timedelta(minutes=config.ACCESS_TOKEN_EXPIRE_MINUTES)
    return {
        "access_token": create_access_token(
            data={"owner_id": owner.id}, expires_delta=access_token_expires
        )
    }


@router.put("/owners", response_model=OwnerDetails)
async def update_owner(
        *,
        db: Session = Depends(get_db),
        data: OwnerUpdate,
        current_owner: DBOwnerModel = Depends(get_current_owner)
):
    with expected_integrity_error(db, detail="There was a conflict with an existing owner", debug=False):
        owner = update_owner_info(db, data=data, owner=current_owner)
    return owner
