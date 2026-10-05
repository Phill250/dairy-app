import uuid
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.models.cow import CowModel


class CowRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, cow: CowModel) -> CowModel:
        self.db.add(cow)
        self.db.commit()
        self.db.refresh(cow)
        return cow

    def update(self, cow: CowModel) -> CowModel:
        self.db.commit()
        self.db.refresh(cow)
        return cow

    def delete(self, cow: CowModel) -> None:
        self.db.delete(cow)
        self.db.commit()

    def get_by_id(self, cow_id: uuid.UUID) -> CowModel | None:
        return self.db.query(CowModel).filter(CowModel.id == cow_id).first()

    def get_all_for_farmer(self, farmer_id: uuid.UUID) -> list[CowModel]:
        return self.db.query(CowModel).filter(CowModel.farmer_id == farmer_id).all()

    def count_all(self) -> int:
        return self.db.query(func.count(CowModel.id)).scalar()
    
    def count_for_farmer(self, farmer_id: uuid.UUID) -> int:
        return self.db.query(func.count(CowModel.id)).filter(CowModel.farmer_id == farmer_id).scalar()