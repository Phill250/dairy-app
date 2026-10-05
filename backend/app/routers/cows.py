import uuid
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.core.limiter import limiter
from app.repository.cow_repository import CowRepository
from app.services.cow_service import CowService
from app.schemas.cow import CowCreate, CowUpdate, CowRead
from app.models.user import UserModel

router = APIRouter(prefix="/api/cows", tags=["cows"])


def get_cow_service(db: Session = Depends(get_db)) -> CowService:
    return CowService(CowRepository(db))


@router.get("", response_model=list[CowRead])
@limiter.limit("120/minute")
def list_cows(
    request: Request,
    service: CowService = Depends(get_cow_service),
    current_user: UserModel = Depends(get_current_user),
):
    return service.list_cows_for_farmer(current_user.id)


@router.get("/{cow_id}", response_model=CowRead)
@limiter.limit("120/minute")
def read_cow(
    request: Request,
    cow_id: uuid.UUID,
    service: CowService = Depends(get_cow_service),
    current_user: UserModel = Depends(get_current_user),
):
    cow = service.get_cow_for_farmer(cow_id, current_user.id)
    if cow is None:
        raise HTTPException(status_code=404, detail="Cow not found")
    return cow


@router.post("", response_model=CowRead, status_code=201)
@limiter.limit("30/hour")
def create_cow(
    request: Request,
    cow_in: CowCreate,
    service: CowService = Depends(get_cow_service),
    current_user: UserModel = Depends(get_current_user),
):
    return service.create_cow(cow_in, farmer_id=current_user.id)


@router.patch("/{cow_id}", response_model=CowRead)
@limiter.limit("60/hour")
def update_cow(
    request: Request,
    cow_id: uuid.UUID,
    cow_in: CowUpdate,
    service: CowService = Depends(get_cow_service),
    current_user: UserModel = Depends(get_current_user),
):
    updated = service.update_cow(cow_id, cow_in, farmer_id=current_user.id)
    if updated is None:
        raise HTTPException(status_code=404, detail="Cow not found")
    return updated


@router.delete("/{cow_id}", status_code=204)
@limiter.limit("60/hour")
def delete_cow(
    request: Request,
    cow_id: uuid.UUID,
    service: CowService = Depends(get_cow_service),
    current_user: UserModel = Depends(get_current_user),
):
    ok = service.delete_cow(cow_id, current_user.id)
    if not ok:
        raise HTTPException(status_code=404, detail="Cow not found")