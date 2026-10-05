from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import require_role
from app.core.limiter import limiter
from app.repository.user_repository import UserRepository
from app.repository.cow_repository import CowRepository
from app.repository.log_repository import LogRepository
from app.services.metrics_service import MetricsService
from app.schemas.metrics import MetricsRead
from app.schemas.admin import AdminUserSummary
from app.models.user import UserModel, UserRole

router = APIRouter(prefix="/api/admin", tags=["admin"])


def get_metrics_service(db: Session = Depends(get_db)) -> MetricsService:
    return MetricsService(UserRepository(db), CowRepository(db), LogRepository(db))


@router.get("/metrics", response_model=MetricsRead)
@limiter.limit("60/minute")
def get_metrics(
    request: Request,
    service: MetricsService = Depends(get_metrics_service),
    _current_user: UserModel = Depends(require_role(UserRole.admin)),
):
    return service.get_metrics()


@router.get("/users", response_model=list[AdminUserSummary])
@limiter.limit("60/minute")
def list_users(
    request: Request,
    service: MetricsService = Depends(get_metrics_service),
    _current_user: UserModel = Depends(require_role(UserRole.admin)),
):
    """Non-identifying account activity view, no names or emails."""
    return service.list_farmer_summaries()