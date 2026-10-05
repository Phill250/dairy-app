from app.repository.user_repository import UserRepository
from app.repository.cow_repository import CowRepository
from app.repository.log_repository import LogRepository
from app.models.user import UserRole
from app.schemas.metrics import MetricsRead
from app.schemas.admin import AdminUserSummary


class MetricsService:
    def __init__(self, user_repo: UserRepository, cow_repo: CowRepository, log_repo: LogRepository):
        self.user_repo = user_repo
        self.cow_repo = cow_repo
        self.log_repo = log_repo

    def get_metrics(self) -> MetricsRead:
        return MetricsRead(
            total_farmers=self.user_repo.count_by_role(UserRole.farmer),
            total_cows=self.cow_repo.count_all(),
            total_logs=self.log_repo.count_all(),
            average_total_milk=self.log_repo.average_total_milk(),
            average_feed=self.log_repo.average_feed(),
            average_predicted_yield=self.log_repo.average_predicted_yield(),
            ml_model_usage_rate=self.log_repo.ml_model_usage_rate(),
            status_breakdown=self.log_repo.status_breakdown(),
        )

    def list_farmer_summaries(self) -> list[AdminUserSummary]:
        farmers = self.user_repo.list_farmers()
        return [
            AdminUserSummary(
                id=farmer.id,
                created_at=farmer.created_at,
                cow_count=self.cow_repo.count_for_farmer(farmer.id),
                log_count=self.log_repo.count_for_farmer(farmer.id),
            )
            for farmer in farmers
        ]