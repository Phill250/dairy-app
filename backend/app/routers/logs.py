import uuid
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.core.limiter import limiter
from app.repository.log_repository import LogRepository
from app.repository.cow_repository import CowRepository
from app.services.log_service import LogService
from app.schemas.log import LogCreate, LogRead, LogUpdate, PredictionRequest, PredictionResponse
from app.models.user import UserModel

router = APIRouter(prefix="/api/logs", tags=["logs"])


def get_log_service(db: Session = Depends(get_db)) -> LogService:
    return LogService(LogRepository(db), CowRepository(db))


@router.get("", response_model=list[LogRead])
@limiter.limit("120/minute")
def read_logs(
    request: Request,
    service: LogService = Depends(get_log_service),
    current_user: UserModel = Depends(get_current_user),
):
    return service.list_logs_for_farmer(current_user.id)


@router.get("/{log_id}", response_model=LogRead)
@limiter.limit("120/minute")
def read_log(
    request: Request,
    log_id: uuid.UUID,
    service: LogService = Depends(get_log_service),
    current_user: UserModel = Depends(get_current_user),
):
    log = service.get_log_for_farmer(log_id, current_user.id)
    if log is None:
        raise HTTPException(status_code=404, detail="Log not found")
    return log


@router.post("", response_model=LogRead, status_code=201)
@limiter.limit("100/hour")
def create_log(
    request: Request,
    log_in: LogCreate,
    service: LogService = Depends(get_log_service),
    current_user: UserModel = Depends(get_current_user),
):
    try:
        return service.create_log(log_in, farmer_id=current_user.id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.patch("/{log_id}", response_model=LogRead)
@limiter.limit("100/hour")
def update_log(
    request: Request,
    log_id: uuid.UUID,
    log_in: LogUpdate,
    service: LogService = Depends(get_log_service),
    current_user: UserModel = Depends(get_current_user),
):
    try:
        updated = service.update_log(log_id, log_in, farmer_id=current_user.id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    if updated is None:
        raise HTTPException(status_code=404, detail="Log not found")
    return updated


@router.delete("/{log_id}", status_code=204)
@limiter.limit("100/hour")
def delete_log(
    request: Request,
    log_id: uuid.UUID,
    service: LogService = Depends(get_log_service),
    current_user: UserModel = Depends(get_current_user),
):
    ok = service.delete_log(log_id, current_user.id)
    if not ok:
        raise HTTPException(status_code=404, detail="Log not found")


@router.post("/predict", response_model=PredictionResponse)
@limiter.limit("60/minute")
def predict_yield(
    request: Request,
    payload: PredictionRequest,
    service: LogService = Depends(get_log_service),
    current_user: UserModel = Depends(get_current_user),
):
    result = service.predict(payload.cow_id, payload.feed, payload.milking_times, current_user.id)
    if result is None:
        raise HTTPException(status_code=404, detail="Cow not found")
    expected, model_used = result
    return PredictionResponse(expected_yield=expected, model_used=model_used)