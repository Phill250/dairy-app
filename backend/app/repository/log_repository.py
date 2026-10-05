import uuid
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.models.log import LogModel
from app.models.cow import CowModel


class LogRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, log_model: LogModel) -> LogModel:
        self.db.add(log_model)
        self.db.commit()
        self.db.refresh(log_model)
        return log_model

    def update(self, log_model: LogModel) -> LogModel:
        self.db.commit()
        self.db.refresh(log_model)
        return log_model

    def get_by_id(self, log_id: uuid.UUID) -> LogModel | None:
        return self.db.query(LogModel).filter(LogModel.id == log_id).first()

    def get_all_for_farmer(self, farmer_id: uuid.UUID, limit: int = 200) -> list[LogModel]:
        return (
            self.db.query(LogModel)
            .join(CowModel, LogModel.cow_id == CowModel.id)
            .filter(CowModel.farmer_id == farmer_id)
            .order_by(LogModel.date.desc())
            .limit(limit)
            .all()
        )

    def get_all_for_cow(self, cow_id: uuid.UUID, limit: int = 200) -> list[LogModel]:
        return (
            self.db.query(LogModel)
            .filter(LogModel.cow_id == cow_id)
            .order_by(LogModel.date.desc())
            .limit(limit)
            .all()
        )
    def delete(self, log_model: LogModel) -> None:
        self.db.delete(log_model)
        self.db.commit()

    # --- Aggregate queries for admin metrics — never return individual rows ---

    def count_all(self) -> int:
        return self.db.query(func.count(LogModel.id)).scalar()

    def average_total_milk(self) -> float | None:
        return self.db.query(func.avg(LogModel.total_milk)).scalar()

    def average_feed(self) -> float | None:
        return self.db.query(func.avg(LogModel.feed)).scalar()

    def average_predicted_yield(self) -> float | None:
        return self.db.query(func.avg(LogModel.predicted_yield)).filter(
            LogModel.predicted_yield.isnot(None)
        ).scalar()

    def ml_model_usage_rate(self) -> float:
        total = self.count_all()
        if total == 0:
            return 0.0
        used = self.db.query(func.count(LogModel.id)).filter(LogModel.used_ml_model.is_(True)).scalar()
        return round(used / total, 3)

    def status_breakdown(self) -> dict[str, int]:
        rows = self.db.query(LogModel.status, func.count(LogModel.id)).group_by(LogModel.status).all()
        return {status: count for status, count in rows}
    
    def count_for_farmer(self, farmer_id: uuid.UUID) -> int:
        return (
            self.db.query(func.count(LogModel.id))
            .join(CowModel, LogModel.cow_id == CowModel.id)
            .filter(CowModel.farmer_id == farmer_id)
            .scalar()
        )